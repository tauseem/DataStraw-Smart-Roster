
from datetime import timedelta

from django.db import transaction
from django.db.models import Count, Q

from .models import (
    Employee,
    ShiftAssignment,
    StaffingRequirement,
    EmployeeAllocation,
    WeeklyOff,
    PublicHoliday,
    CompOff,
    Attendance,
    LeaveRequest,
)

from .serializers import ShiftAssignmentSerializer


# ============================================================
# EMPLOYEE AVAILABILITY
# ============================================================

def get_employee_unavailability_reason(employee, roster_date):

    weekly_off = WeeklyOff.objects.filter(
        employee=employee,
        weekday=roster_date.weekday(),
        effective_from__lte=roster_date,
        is_active=True,
    ).filter(
        Q(effective_until__isnull=True)
        | Q(effective_until__gte=roster_date)
    ).exists()

    if weekly_off:
        return "Weekly off"

    leave = LeaveRequest.objects.filter(
        employee=employee,
        status="APPROVED",
        start_date__lte=roster_date,
        end_date__gte=roster_date,
    ).exists()

    if leave:
        return "Approved leave"

    comp_off = CompOff.objects.filter(
        employee=employee,
        usable_on=roster_date,
        status="APPROVED",
    ).exists()

    if comp_off:
        return "Approved compensatory off"

    return None


# ============================================================
# PUBLIC HOLIDAYS
# ============================================================

def is_public_holiday(roster_date):

    return PublicHoliday.objects.filter(
        holiday_date=roster_date,
        region="IN",
        is_active=True,
    ).exists()


# ============================================================
# BRAND / PROCESS WORKING DAYS
# ============================================================

def is_brand_process_working_on_date(brand_process, roster_date):

    if not brand_process:
        return True

    if not brand_process.is_active:
        return False

    if not brand_process.brand.is_active:
        return False

    if not brand_process.process.is_active:
        return False

    if roster_date.weekday() not in brand_process.working_days:
        return False

    holiday = is_public_holiday(roster_date)

    if holiday and brand_process.holiday_policy == "OFF":
        return False

    return True


# ============================================================
# REQUIREMENT KEY
# ============================================================

def get_requirement_key(requirement):

    return (
        requirement.shift_id,
        requirement.brand_process_id,
    )


# ============================================================
# EMPLOYEE ALLOCATION CHECK
# ============================================================

def employee_has_required_allocation(employee, requirement, roster_date):

    if not requirement.brand_process_id:
        return True

    return EmployeeAllocation.objects.filter(
        employee=employee,
        brand_process_id=requirement.brand_process_id,
        is_active=True,
        allocation_start__lte=roster_date,
    ).filter(
        Q(allocation_end__isnull=True)
        | Q(allocation_end__gte=roster_date)
    ).exists()


# ============================================================
# AUTOMATIC ROSTER GENERATION
# ============================================================

@transaction.atomic
def generate_roster(roster_date):

    generated = []
    rebalanced = []
    skipped = []
    shortages = []

    # --------------------------------------------------------
    # 1. GET STAFFING REQUIREMENTS
    # --------------------------------------------------------

    all_requirements = list(
        StaffingRequirement.objects.filter(
            requirement_date=roster_date,
            shift__is_active=True,
        ).select_related(
            "shift",
            "brand_process",
            "brand_process__brand",
            "brand_process__process",
        ).order_by(
            "shift__start_time"
        )
    )

    requirements = [
        requirement
        for requirement in all_requirements
        if is_brand_process_working_on_date(
            requirement.brand_process,
            roster_date,
        )
    ]

    if not requirements:

        return {
            "success": False,
            "date": str(roster_date),
            "message": (
                "No applicable staffing requirements found "
                "for this date."
            ),
            "generated_count": 0,
            "rebalanced_count": 0,
            "preserved_count": 0,
            "total_assigned": 0,
            "generated": [],
            "rebalanced": [],
            "shortages": [],
            "skipped": [],
            "conflicts": [],
        }

    # --------------------------------------------------------
    # 2. GET EXISTING ASSIGNMENTS
    # --------------------------------------------------------

    existing_assignments = list(
        ShiftAssignment.objects.filter(
            shift_date=roster_date,
        ).exclude(
            status="CANCELLED"
        ).select_related(
            "employee",
            "shift",
            "brand_process",
        )
    )

    assigned_employee_ids = {
        assignment.employee_id
        for assignment in existing_assignments
    }

    preserved_count = len(existing_assignments)

    # --------------------------------------------------------
    # 2b. CHECK EXISTING ASSIGNMENTS FOR CONFLICTS
    # --------------------------------------------------------

    # An assignment already on the roster can still conflict
    # with leave, weekly offs, or comp-offs. Report these
    # instead of silently keeping them.

    conflicts = []

    for assignment in existing_assignments:

        reason = get_employee_unavailability_reason(
            assignment.employee,
            roster_date,
        )

        if reason:
            conflicts.append({
                "employee": assignment.employee.full_name,
                "employee_id": assignment.employee.employee_id,
                "shift": assignment.shift.shift_name,
                "reason": reason,
            })

    # --------------------------------------------------------
    # 3. COUNT EXISTING ASSIGNMENTS
    # --------------------------------------------------------

    assigned_counts = {}

    for requirement in requirements:

        requirement_key = get_requirement_key(requirement)

        assigned_counts[requirement_key] = sum(
            1
            for assignment in existing_assignments
            if (
                assignment.shift_id == requirement.shift_id
                and assignment.brand_process_id
                == requirement.brand_process_id
            )
        )

    # --------------------------------------------------------
    # 4. CALCULATE STAFFING NEEDS
    # --------------------------------------------------------

    remaining_needs = {}

    for requirement in requirements:

        requirement_key = get_requirement_key(requirement)

        remaining_needs[requirement_key] = max(
            0,
            requirement.required_employees
            - assigned_counts[requirement_key],
        )

    # --------------------------------------------------------
    # 5. FIND UNASSIGNED ACTIVE EMPLOYEES
    # --------------------------------------------------------

    recent_start = roster_date - timedelta(days=7)

    employees = list(
        Employee.objects.filter(
            employment_status="ACTIVE",
        ).exclude(
            id__in=assigned_employee_ids,
        ).annotate(
            recent_assignments=Count(
                "shift_assignments",
                filter=Q(
                    shift_assignments__shift_date__gte=recent_start,
                    shift_assignments__shift_date__lt=roster_date,
                    shift_assignments__status="SCHEDULED",
                ),
            ),
        ).order_by(
            "recent_assignments",
            "created_at",
            "id",
        ).distinct()
    )

    # --------------------------------------------------------
    # 6. ASSIGN AVAILABLE EMPLOYEES
    # --------------------------------------------------------

    progress = True

    while progress:

        progress = False

        for requirement in requirements:

            shift = requirement.shift
            requirement_key = get_requirement_key(requirement)

            if remaining_needs[requirement_key] <= 0:
                continue

            for employee in employees:

                if employee.id in assigned_employee_ids:
                    continue

                # Check weekly off, leave, and comp-off.
                unavailability_reason = (
                    get_employee_unavailability_reason(
                        employee,
                        roster_date,
                    )
                )

                if unavailability_reason:

                    skipped.append({
                        "employee": employee.full_name,
                        "employee_id": employee.employee_id,
                        "shift": shift.shift_name,
                        "reason": unavailability_reason,
                    })

                    continue

                # Check brand/process allocation.
                if not employee_has_required_allocation(
                    employee,
                    requirement,
                    roster_date,
                ):

                    skipped.append({
                        "employee": employee.full_name,
                        "employee_id": employee.employee_id,
                        "shift": shift.shift_name,
                        "reason": (
                            "Not allocated to the required "
                            "brand/process"
                        ),
                    })

                    continue

                assignment_data = {
                    "employee": employee.id,
                    "shift": shift.id,
                    "brand_process": requirement.brand_process_id,
                    "shift_date": roster_date,
                    "status": "SCHEDULED",
                }

                serializer = ShiftAssignmentSerializer(
                    data=assignment_data
                )

                if serializer.is_valid():

                    assignment = serializer.save()

                    generated.append({
                        "assignment_id": assignment.id,
                        "employee": employee.full_name,
                        "employee_id": employee.employee_id,
                        "shift": shift.shift_name,
                        "brand": (
                            requirement.brand_process.brand.name
                            if requirement.brand_process
                            else None
                        ),
                        "process": (
                            requirement.brand_process.process.name
                            if requirement.brand_process
                            else None
                        ),
                        "date": str(roster_date),
                    })

                    assigned_employee_ids.add(employee.id)

                    assigned_counts[requirement_key] += 1
                    remaining_needs[requirement_key] -= 1

                    progress = True
                    break

                skipped.append({
                    "employee": employee.full_name,
                    "employee_id": employee.employee_id,
                    "shift": shift.shift_name,
                    "errors": serializer.errors,
                })

    # --------------------------------------------------------
    # 7. AUTOMATIC SHIFT REBALANCING
    # --------------------------------------------------------

    # Rebalance only after trying to use unassigned employees.
    # Only scheduled assignments without attendance can be moved.

    for target_requirement in requirements:

        target_key = get_requirement_key(target_requirement)

        while remaining_needs[target_key] > 0:

            donor_found = False

            # Look for another requirement with surplus staff.
            for donor_requirement in requirements:

                donor_key = get_requirement_key(donor_requirement)

                if donor_key == target_key:
                    continue

                donor_surplus = (
                    assigned_counts[donor_key]
                    - donor_requirement.required_employees
                )

                if donor_surplus <= 0:
                    continue

                # Find an eligible existing assignment to move.
                donor_assignments = [
                    assignment
                    for assignment in existing_assignments
                    if (
                        assignment.shift_id == donor_requirement.shift_id
                        and assignment.brand_process_id
                        == donor_requirement.brand_process_id
                        and assignment.status == "SCHEDULED"
                    )
                ]

                for assignment in donor_assignments:

                    # Never move an assignment that already has attendance.
                    if Attendance.objects.filter(
                        assignment=assignment
                    ).exists():

                        continue

                    employee = assignment.employee

                    # Check target weekly off, leave, and comp-off.
                    unavailability_reason = (
                        get_employee_unavailability_reason(
                            employee,
                            roster_date,
                        )
                    )

                    if unavailability_reason:
                        continue

                    # Check target brand/process allocation.
                    if not employee_has_required_allocation(
                        employee,
                        target_requirement,
                        roster_date,
                    ):
                        continue

                    old_shift_name = assignment.shift.shift_name

                    old_brand = (
                        assignment.brand_process.brand.name
                        if assignment.brand_process
                        else None
                    )

                    old_process = (
                        assignment.brand_process.process.name
                        if assignment.brand_process
                        else None
                    )

                    # Update the existing assignment.
                    update_data = {
                        "shift": target_requirement.shift_id,
                        "brand_process": (
                            target_requirement.brand_process_id
                        ),
                    }

                    serializer = ShiftAssignmentSerializer(
                        instance=assignment,
                        data=update_data,
                        partial=True,
                    )

                    if not serializer.is_valid():

                        skipped.append({
                            "employee": employee.full_name,
                            "employee_id": employee.employee_id,
                            "shift": target_requirement.shift.shift_name,
                            "reason": (
                                "Rebalancing validation failed"
                            ),
                            "errors": serializer.errors,
                        })

                        continue

                    updated_assignment = serializer.save()

                    # Update in-memory assignment information.
                    assignment.shift = target_requirement.shift
                    assignment.shift_id = (
                        target_requirement.shift_id
                    )

                    assignment.brand_process = (
                        target_requirement.brand_process
                    )

                    assignment.brand_process_id = (
                        target_requirement.brand_process_id
                    )

                    # Update staffing counts.
                    assigned_counts[donor_key] -= 1
                    assigned_counts[target_key] += 1

                    remaining_needs[target_key] -= 1

                    rebalanced.append({
                        "assignment_id": updated_assignment.id,
                        "employee": employee.full_name,
                        "employee_id": employee.employee_id,
                        "from_shift": old_shift_name,
                        "to_shift": target_requirement.shift.shift_name,
                        "from_brand": old_brand,
                        "from_process": old_process,
                        "to_brand": (
                            target_requirement.brand_process.brand.name
                            if target_requirement.brand_process
                            else None
                        ),
                        "to_process": (
                            target_requirement.brand_process.process.name
                            if target_requirement.brand_process
                            else None
                        ),
                        "date": str(roster_date),
                    })

                    donor_found = True
                    break

                if donor_found:
                    break

            # No eligible surplus employee was available.
            if not donor_found:
                break

    # --------------------------------------------------------
    # 8. CALCULATE STAFFING SHORTAGES
    # --------------------------------------------------------

    for requirement in requirements:

        requirement_key = get_requirement_key(requirement)

        required = requirement.required_employees
        assigned = assigned_counts[requirement_key]

        shortage = max(0, required - assigned)

        if shortage > 0:

            shortages.append({
                "shift": requirement.shift.shift_name,
                "brand": (
                    requirement.brand_process.brand.name
                    if requirement.brand_process
                    else "Not specified"
                ),
                "process": (
                    requirement.brand_process.process.name
                    if requirement.brand_process
                    else "Not specified"
                ),
                "required": required,
                "assigned": assigned,
                "shortage": shortage,
            })

    # --------------------------------------------------------
    # 9. RETURN RESULTS
    # --------------------------------------------------------

    roster_is_clean = not shortages and not conflicts

    return {
        "success": roster_is_clean,
        "date": str(roster_date),

        "message": (
            "Roster generated successfully."
            if roster_is_clean
            else "Roster has issues that need attention."
        ),

        "generated_count": len(generated),
        "rebalanced_count": len(rebalanced),
        "preserved_count": preserved_count,

        "total_assigned": sum(
            assigned_counts.values()
        ),

        "generated": generated,
        "rebalanced": rebalanced,
        "shortages": shortages,
        "skipped": skipped,
        "conflicts": conflicts,
    }