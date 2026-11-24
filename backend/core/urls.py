from .monthly_views import monthly_roster_api
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    health_check,
    generate_roster_api,
    roster_calendar_api,
    dashboard_summary_api,
    EmployeeViewSet,
    ShiftViewSet,
    ShiftAssignmentViewSet,
    StaffingRequirementViewSet,
    LeaveRequestViewSet,
    AttendanceViewSet,
    BrandViewSet,
    ProcessViewSet,
    PodViewSet,
    BrandProcessViewSet,
    EmployeeAllocationViewSet,
    PublicHolidayViewSet,
    WeeklyOffViewSet,
    CompOffViewSet,
    CoverageRequirementViewSet,
)


router = DefaultRouter()

router.register(
    "employees",
    EmployeeViewSet,
    basename="employee"
)

router.register(
    "shifts",
    ShiftViewSet,
    basename="shift"
)

router.register(
    "assignments",
    ShiftAssignmentViewSet,
    basename="assignment"
)

router.register(
    "staffing-requirements",
    StaffingRequirementViewSet,
    basename="staffing-requirement"
)

router.register(
    "leave-requests",
    LeaveRequestViewSet,
    basename="leave-request"
)

router.register(
    "attendance",
    AttendanceViewSet,
    basename="attendance"
)

router.register("brands", BrandViewSet)
router.register("processes", ProcessViewSet)
router.register("pods", PodViewSet)
router.register("brand-processes", BrandProcessViewSet)
router.register("employee-allocations", EmployeeAllocationViewSet)
router.register("public-holidays", PublicHolidayViewSet)
router.register("weekly-offs", WeeklyOffViewSet)
router.register("comp-offs", CompOffViewSet)
router.register("coverage-requirements", CoverageRequirementViewSet)

urlpatterns = [
    path("", include(router.urls)),

    path("health/", health_check, name="health-check"),

    path(
        "generate-roster/",
        generate_roster_api,
        name="generate-roster"
    ),

    path(
        "roster-calendar/",
        roster_calendar_api,
        name="roster-calendar"
    ),

    path(
        "dashboard-summary/",
        dashboard_summary_api,
        name="dashboard-summary"
    ),
    path(
        "monthly-roster/",
        monthly_roster_api,
        name="monthly-roster"
    ),
]