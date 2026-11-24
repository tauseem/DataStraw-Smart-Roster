from calendar import monthrange
from collections import defaultdict
from datetime import date, timedelta

from rest_framework.decorators import api_view
from rest_framework.response import Response

from .models import (
    CompOff,
    Employee,
    EmployeeAllocation,
    LeaveRequest,
    Pod,
    PublicHoliday,
    ShiftAssignment,
    StaffingRequirement,
    WeeklyOff,
)
from .roster_service import (
    generate_roster_for_month,
    is_brand_process_working_on_date,
)

WEEKDAY_NAMES = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]


def _dates_between(start, end):
    current = start
    while current <= end:
        yield current
        current += timedelta(days=1)


def _group(items, key):
    groups = defaultdict(list)
    for item in items:
        groups[item[key]].append(item)
    return dict(sorted(groups.items()))


def _weekly_off_active(weekly_off, day):
    return (
        weekly_off.weekday == day.weekday()
        and weekly_off.effective_from <= day
        and (
            weekly_off.effective_until is None
            or weekly_off.effective_until >= day
        )
    )


@api_view(["GET", "POST"])
def monthly_roster_api(request):

    source = request.data if request.method == "POST" else request.query_params

    try:
        year = int(source.get("year"))
        month = int(source.get("month"))
    except (TypeError, ValueError):
        return Response(
            {"success": False, "message": "year and month are required."},
            status=400,
        )

    if not 1 <= month <= 12:
        return Response(
            {"success": False, "message": "month must be between 1 and 12."},
            status=400,
        )

    generation = None

    if request.method == "POST":
        result = generate_roster_for_month(year, month)
        generation = {
            "days": result["days"],
            "days_with_issues": result["days_with_issues"],
        }

    last_day = monthrange(year, month)[1]
    start = date(year, month, 1)
    end = date(year, month, last_day)

    # Pod for each employee, from their active allocation.
    pod_for_employee = {}
    allocations = EmployeeAllocation.objects.filter(
        is_active=True,
    ).select_related("employee", "pod")

    for allocation in allocations:
        if allocation.pod and allocation.employee_id not in pod_for_employee:
            pod_for_employee[allocation.employee_id] = allocation.pod.name

    assignments = (
        ShiftAssignment.objects
        .filter(shift_date__range=(start, end))
        .exclude(status="CANCELLED")
        .select_related(
            "employee",
            "shift",
            "brand_process__brand",
            "brand_process__process",
        )
        .order_by("shift_date", "employee__employee_id")
    )

    rows = []
    for assignment in assignments:
        bp = assignment.brand_process
        rows.append({
            "assignment_id": assignment.id,
            "date": str(assignment.shift_date),
            "employee_id": assignment.employee.employee_id,
            "employee": assignment.employee.full_name,
            "pod": pod_for_employee.get(assignment.employee_id, "Unassigned"),
            "brand": bp.brand.name if bp else "Not specified",
            "process": bp.process.name if bp else "Not specified",
            "brand_process_id": assignment.brand_process_id,
            "shift": assignment.shift.shift_name,
            "status": assignment.status,
        })

    # Coverage: required versus assigned, on working days only.
    assigned_counts = defaultdict(int)
    for row in rows:
        assigned_counts[(row["date"], row["brand_process_id"])] += 1

    requirements = (
        StaffingRequirement.objects
        .filter(
            requirement_date__range=(start, end),
            brand_process__isnull=False,
        )
        .select_related("brand_process__brand", "brand_process__process")
    )

    coverage = []
    for requirement in requirements:
        bp = requirement.brand_process

        if not is_brand_process_working_on_date(bp, requirement.requirement_date):
            continue

        assigned = assigned_counts[(str(requirement.requirement_date), bp.id)]

        coverage.append({
            "date": str(requirement.requirement_date),
            "brand": bp.brand.name,
            "process": bp.process.name,
            "required": requirement.required_employees,
            "assigned": assigned,
            "status": "OK" if assigned >= requirement.required_employees else "SHORT",
        })

    coverage.sort(key=lambda item: (item["date"], item["brand"], item["process"]))

    # Employee calendars: working, leave, weekly off, comp-off, holiday.
    weekly_offs = list(
        WeeklyOff.objects.filter(is_active=True, effective_from__lte=end)
        .select_related("employee")
    )

    leaves = list(
        LeaveRequest.objects.filter(
            status="APPROVED",
            start_date__lte=end,
            end_date__gte=start,
        ).select_related("employee")
    )

    comp_offs = list(
        CompOff.objects.filter(
            status="APPROVED",
            usable_on__range=(start, end),
        ).select_related("employee")
    )

    holidays = {
        holiday.holiday_date: holiday.name
        for holiday in PublicHoliday.objects.filter(
            holiday_date__range=(start, end),
            region="IN",
            is_active=True,
        )
    }

    rows_by_employee = defaultdict(dict)
    for row in rows:
        rows_by_employee[row["employee_id"]][row["date"]] = row

    employee_views = []

    for employee in Employee.objects.order_by("employee_id"):
        emp_offs = [w for w in weekly_offs if w.employee_id == employee.id]
        emp_leaves = [l for l in leaves if l.employee_id == employee.id]
        emp_comp = [c for c in comp_offs if c.employee_id == employee.id]

        leave_dates = set()
        for leave in emp_leaves:
            leave_dates.update(
                _dates_between(
                    max(leave.start_date, start),
                    min(leave.end_date, end),
                )
            )

        comp_dates = {c.usable_on for c in emp_comp}
        worked = rows_by_employee.get(employee.employee_id, {})

        calendar_days = []

        for day in _dates_between(start, end):
            key = str(day)

            if key in worked:
                status = "Working"
                detail = f"{worked[key]['brand']} - {worked[key]['process']}"
            elif day in leave_dates:
                status, detail = "Approved leave", None
            elif day in comp_dates:
                status, detail = "Compensatory off", None
            elif any(_weekly_off_active(w, day) for w in emp_offs):
                status, detail = "Weekly off", None
            elif day in holidays:
                status, detail = "Public holiday", holidays[day]
            else:
                status, detail = "Not scheduled", None

            calendar_days.append({
                "date": key,
                "status": status,
                "detail": detail,
            })

        employee_views.append({
            "employee_id": employee.employee_id,
            "employee": employee.full_name,
            "weekly_offs": [WEEKDAY_NAMES[w.weekday] for w in emp_offs],
            "calendar": calendar_days,
        })

        pod_leads = {
        pod.name: (pod.lead.full_name if pod.lead else None)
        for pod in Pod.objects.select_related("lead")
    }

    return Response({
        "success": True,
        "year": year,
        "month": month,
        "generation": generation,
        "summary": {
            "assignments": len(rows),
            "working_slots": len(coverage),
            "short_slots": sum(1 for item in coverage if item["status"] == "SHORT"),
        },
        "company": _group(rows, "date"),
        "pods": _group(rows, "pod"),
        "brands": _group(rows, "brand"),
        "processes": _group(rows, "process"),
        "brand_coverage": _group(coverage, "brand"),
        "coverage": coverage,
        "employees": employee_views,
        "pod_leads": pod_leads,
    })