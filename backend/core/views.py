from datetime import date

from django.db import transaction
from django.utils import timezone

from rest_framework import status, viewsets
from rest_framework.decorators import api_view
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response


from .models import (
    Employee,
    Shift,
    ShiftAssignment,
    StaffingRequirement,
    LeaveRequest,
    Attendance,
    Brand,
    Process,
    Pod,
    BrandProcess,
    EmployeeAllocation,
    PublicHoliday,
    WeeklyOff,
    CompOff,
    CoverageRequirement,
)

from .serializers import (
    EmployeeSerializer,
    ShiftSerializer,
    ShiftAssignmentSerializer,
    StaffingRequirementSerializer,
    LeaveRequestSerializer,
    AttendanceSerializer,
    BrandSerializer,
    ProcessSerializer,
    PodSerializer,
    BrandProcessSerializer,
    EmployeeAllocationSerializer,
    PublicHolidaySerializer,
    WeeklyOffSerializer,
    CompOffSerializer,
    CoverageRequirementSerializer,
)

from .roster_service import generate_roster


@api_view(["GET"])
def health_check(request):
    return Response({
        "success": True,
        "project": "DataStraw Smart Roster",
        "status": "Healthy",
        "message": "Backend API is running successfully",
    })


# --------------------------------------------------
# EMPLOYEE MANAGEMENT
# --------------------------------------------------

class EmployeeViewSet(viewsets.ModelViewSet):
    queryset = Employee.objects.all().order_by("-created_at")
    serializer_class = EmployeeSerializer


# --------------------------------------------------
# SHIFT MANAGEMENT
# --------------------------------------------------

class ShiftViewSet(viewsets.ModelViewSet):
    queryset = Shift.objects.all().order_by("start_time")
    serializer_class = ShiftSerializer


# --------------------------------------------------
# SHIFT ASSIGNMENT MANAGEMENT
# --------------------------------------------------

class ShiftAssignmentViewSet(viewsets.ModelViewSet):
    queryset = (
        ShiftAssignment.objects
        .select_related("employee", "shift")
        .all()
        .order_by("-shift_date")
    )

    serializer_class = ShiftAssignmentSerializer


# --------------------------------------------------
# STAFFING REQUIREMENT MANAGEMENT
# --------------------------------------------------

class StaffingRequirementViewSet(viewsets.ModelViewSet):
    queryset = (
        StaffingRequirement.objects
        .select_related("shift")
        .all()
        .order_by("-requirement_date")
    )

    serializer_class = StaffingRequirementSerializer


# --------------------------------------------------
# LEAVE MANAGEMENT
# --------------------------------------------------

class LeaveRequestViewSet(viewsets.ModelViewSet):
    queryset = (
        LeaveRequest.objects
        .select_related("employee")
        .all()
        .order_by("-created_at")
    )

    serializer_class = LeaveRequestSerializer

    def perform_update(self, serializer):
        """
        Prevent approval of leave when the employee
        already has non-cancelled roster assignments
        during the requested leave period.
        """

        leave = self.get_object()

        new_status = serializer.validated_data.get(
            "status",
            leave.status
        )

        if new_status == "APPROVED":
            start_date = serializer.validated_data.get(
                "start_date",
                leave.start_date
            )

            end_date = serializer.validated_data.get(
                "end_date",
                leave.end_date
            )

            conflict = ShiftAssignment.objects.filter(
                employee=leave.employee,
                shift_date__range=(start_date, end_date),
            ).exclude(
                status="CANCELLED"
            )

            if conflict.exists():
                raise ValidationError({
                    "status": (
                        "Leave cannot be approved because this "
                        "employee already has roster assignments "
                        "during the requested leave period. "
                        "Resolve those assignments first."
                    )
                })

        serializer.save()


# --------------------------------------------------
# ATTENDANCE MANAGEMENT
# --------------------------------------------------

class AttendanceViewSet(viewsets.ModelViewSet):
    queryset = (
        Attendance.objects
        .select_related(
            "assignment",
            "assignment__employee",
            "assignment__shift",
        )
        .all()
        .order_by("-created_at")
    )

    serializer_class = AttendanceSerializer


# --------------------------------------------------
# AUTOMATIC ROSTER GENERATION
# --------------------------------------------------

@api_view(["POST"])
def generate_roster_api(request):

    roster_date = request.data.get("date")

    if not roster_date:
        return Response(
            {
                "success": False,
                "message": "Please provide a roster date.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        parsed_date = date.fromisoformat(roster_date)

    except (ValueError, TypeError):
        return Response(
            {
                "success": False,
                "message": "Invalid date. Use YYYY-MM-DD format.",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    result = generate_roster(parsed_date)

    response_status = (
        status.HTTP_200_OK
        if result.get("success")
        else status.HTTP_200_OK
    )

    return Response(result, status=response_status)


# --------------------------------------------------
# ROSTER CALENDAR
# --------------------------------------------------

@api_view(["GET"])
def roster_calendar_api(request):

    roster_date = request.query_params.get("date")

    assignments = (
        ShiftAssignment.objects
        .select_related("employee", "shift")
        .exclude(status="CANCELLED")
        .order_by(
            "shift__start_time",
            "employee__full_name",
        )
    )

    if roster_date:
        try:
            parsed_date = date.fromisoformat(roster_date)

        except (ValueError, TypeError):
            return Response(
                {
                    "success": False,
                    "message": "Invalid date. Use YYYY-MM-DD.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        assignments = assignments.filter(
            shift_date=parsed_date
        )

    results = []

    for assignment in assignments:

        results.append({
            "id": assignment.id,

            "employee_id": assignment.employee.employee_id,
            "employee_name": assignment.employee.full_name,

            "brand": assignment.employee.brand,
            "process": assignment.employee.process,

            "shift_id": assignment.shift.id,
            "shift_name": assignment.shift.shift_name,
            "shift_code": assignment.shift.shift_code,

            "start_time": assignment.shift.start_time.strftime("%H:%M"),
            "end_time": assignment.shift.end_time.strftime("%H:%M"),

            "shift_date": str(assignment.shift_date),
            "status": assignment.status,
        })

    return Response({
        "success": True,
        "count": len(results),
        "assignments": results,
    })


# --------------------------------------------------
# DASHBOARD SUMMARY
# --------------------------------------------------

@api_view(["GET"])
def dashboard_summary_api(request):

    today = date.today()

    total_employees = Employee.objects.count()

    active_employees = Employee.objects.filter(
        employment_status="ACTIVE"
    ).count()

    inactive_employees = Employee.objects.filter(
        employment_status="INACTIVE"
    ).count()

    active_shifts = Shift.objects.filter(
        is_active=True
    ).count()

    today_assignments = ShiftAssignment.objects.filter(
        shift_date=today
    ).exclude(
        status="CANCELLED"
    ).count()

    pending_leaves = LeaveRequest.objects.filter(
        status="PENDING"
    ).count()

    approved_leaves = LeaveRequest.objects.filter(
        status="APPROVED",
        start_date__lte=today,
        end_date__gte=today,
    ).count()

    today_present = Attendance.objects.filter(
        assignment__shift_date=today,
        status="PRESENT",
    ).count()

    today_absent = Attendance.objects.filter(
        assignment__shift_date=today,
        status="ABSENT",
    ).count()

    return Response({
        "success": True,
        "date": str(today),

        "employees": {
            "total": total_employees,
            "active": active_employees,
            "inactive": inactive_employees,
        },

        "shifts": {
            "active": active_shifts,
        },

        "roster": {
            "today_assignments": today_assignments,
        },

        "leaves": {
            "pending": pending_leaves,
            "approved_today": approved_leaves,
        },

        "attendance": {
            "present": today_present,
            "absent": today_absent,
        },
    })


# ==========================================
# ADDITIONAL ROSTER MANAGEMENT VIEWSETS
# ==========================================


class BrandViewSet(viewsets.ModelViewSet):
    queryset = Brand.objects.all().order_by("name")
    serializer_class = BrandSerializer


class ProcessViewSet(viewsets.ModelViewSet):
    queryset = Process.objects.all().order_by("name")
    serializer_class = ProcessSerializer


class PodViewSet(viewsets.ModelViewSet):
    queryset = Pod.objects.select_related("lead").all().order_by("name")
    serializer_class = PodSerializer


class BrandProcessViewSet(viewsets.ModelViewSet):
    queryset = BrandProcess.objects.select_related(
        "brand", "process"
    ).all()
    serializer_class = BrandProcessSerializer


class EmployeeAllocationViewSet(viewsets.ModelViewSet):
    queryset = EmployeeAllocation.objects.select_related(
        "employee", "brand_process", "pod"
    ).all()
    serializer_class = EmployeeAllocationSerializer


class PublicHolidayViewSet(viewsets.ModelViewSet):
    queryset = PublicHoliday.objects.all().order_by("holiday_date")
    serializer_class = PublicHolidaySerializer


class WeeklyOffViewSet(viewsets.ModelViewSet):
    queryset = WeeklyOff.objects.select_related(
        "employee"
    ).all().order_by("effective_from")
    serializer_class = WeeklyOffSerializer


class CompOffViewSet(viewsets.ModelViewSet):
    queryset = CompOff.objects.select_related(
        "employee"
    ).all().order_by("-created_at")
    serializer_class = CompOffSerializer


class CoverageRequirementViewSet(viewsets.ModelViewSet):
    queryset = CoverageRequirement.objects.select_related(
        "brand_process"
    ).all().order_by("requirement_date")
    serializer_class = CoverageRequirementSerializer
