
from django.contrib import admin

from .models import (
    Employee,
    Brand,
    Process,
    Pod,
    BrandProcess,
    EmployeeAllocation,
    PublicHoliday,
    WeeklyOff,
    CompOff,
    CoverageRequirement,
    Shift,
    ShiftAssignment,
    StaffingRequirement,
    LeaveRequest,
    Attendance,
)


# ============================================================
# EMPLOYEE ALLOCATION INLINE
# ============================================================

class EmployeeAllocationInline(admin.TabularInline):
    model = EmployeeAllocation
    extra = 1
    autocomplete_fields = ("brand_process", "pod")


# ============================================================
# EMPLOYEE ADMIN
# ============================================================

@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):

    list_display = (
        "employee_id",
        "full_name",
        "email",
        "brand",
        "process",
        "employment_status",
        "joining_date",
    )

    search_fields = (
        "employee_id",
        "full_name",
        "email",
        "brand",
        "process",
    )

    list_filter = (
        "employment_status",
        "brand",
        "process",
    )

    inlines = [EmployeeAllocationInline]


# ============================================================
# BRAND ADMIN
# ============================================================

@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
    )

    list_filter = (
        "is_active",
    )


# ============================================================
# PROCESS ADMIN
# ============================================================

@admin.register(Process)
class ProcessAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
    )

    list_filter = (
        "is_active",
    )


# ============================================================
# POD ADMIN
# ============================================================

@admin.register(Pod)
class PodAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "code",
        "lead",
        "is_active",
        "created_at",
    )

    search_fields = (
        "name",
        "code",
        "lead__full_name",
        "lead__employee_id",
    )

    list_filter = (
        "is_active",
    )

    autocomplete_fields = ("lead",)


# ============================================================
# BRAND PROCESS ADMIN
# ============================================================

@admin.register(BrandProcess)
class BrandProcessAdmin(admin.ModelAdmin):

    list_display = (
        "brand",
        "process",
        "minimum_staffing",
        "holiday_policy",
        "is_active",
    )

    search_fields = (
        "brand__name",
        "brand__code",
        "process__name",
        "process__code",
    )

    list_filter = (
        "is_active",
        "holiday_policy",
        "brand",
        "process",
    )

    autocomplete_fields = (
        "brand",
        "process",
    )


# ============================================================
# EMPLOYEE ALLOCATION ADMIN
# ============================================================

@admin.register(EmployeeAllocation)
class EmployeeAllocationAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "brand_process",
        "pod",
        "allocation_start",
        "allocation_end",
        "is_active",
    )

    search_fields = (
        "employee__employee_id",
        "employee__full_name",
        "brand_process__brand__name",
        "brand_process__process__name",
        "pod__name",
    )

    list_filter = (
        "is_active",
        "brand_process__brand",
        "brand_process__process",
        "pod",
    )

    autocomplete_fields = (
        "employee",
        "brand_process",
        "pod",
    )


# ============================================================
# PUBLIC HOLIDAY ADMIN
# ============================================================

@admin.register(PublicHoliday)
class PublicHolidayAdmin(admin.ModelAdmin):

    list_display = (
        "name",
        "holiday_date",
        "region",
        "is_active",
    )

    search_fields = (
        "name",
        "region",
    )

    list_filter = (
        "region",
        "is_active",
        "holiday_date",
    )


# ============================================================
# WEEKLY OFF ADMIN
# ============================================================

@admin.register(WeeklyOff)
class WeeklyOffAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "weekday",
        "effective_from",
        "effective_until",
        "is_active",
    )

    search_fields = (
        "employee__employee_id",
        "employee__full_name",
    )

    list_filter = (
        "weekday",
        "is_active",
    )

    autocomplete_fields = ("employee",)


# ============================================================
# COMP OFF ADMIN
# ============================================================

@admin.register(CompOff)
class CompOffAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "earned_on",
        "usable_on",
        "status",
        "created_at",
    )

    search_fields = (
        "employee__employee_id",
        "employee__full_name",
    )

    list_filter = (
        "status",
        "earned_on",
    )

    autocomplete_fields = ("employee",)


# ============================================================
# COVERAGE REQUIREMENT ADMIN
# ============================================================

@admin.register(CoverageRequirement)
class CoverageRequirementAdmin(admin.ModelAdmin):

    list_display = (
        "brand_process",
        "requirement_date",
        "required_employees",
        "created_at",
    )

    search_fields = (
        "brand_process__brand__name",
        "brand_process__process__name",
    )

    list_filter = (
        "requirement_date",
        "brand_process__brand",
        "brand_process__process",
    )

    autocomplete_fields = ("brand_process",)


# ============================================================
# SHIFT ADMIN
# ============================================================

@admin.register(Shift)
class ShiftAdmin(admin.ModelAdmin):

    list_display = (
        "shift_name",
        "shift_code",
        "shift_type",
        "start_time",
        "end_time",
        "is_active",
    )

    search_fields = (
        "shift_name",
        "shift_code",
    )

    list_filter = (
        "shift_type",
        "is_active",
    )


# ============================================================
# SHIFT ASSIGNMENT ADMIN
# ============================================================

@admin.register(ShiftAssignment)
class ShiftAssignmentAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "shift",
        "shift_date",
        "status",
        "created_at",
    )

    search_fields = (
        "employee__employee_id",
        "employee__full_name",
        "shift__shift_name",
    )

    list_filter = (
        "status",
        "shift_date",
        "shift",
    )

    autocomplete_fields = (
        "employee",
        "shift",
    )


# ============================================================
# LEGACY STAFFING REQUIREMENT ADMIN
# ============================================================

@admin.register(StaffingRequirement)
class StaffingRequirementAdmin(admin.ModelAdmin):

    list_display = (
        "shift",
        "requirement_date",
        "required_employees",
        "created_at",
    )

    search_fields = (
        "shift__shift_name",
        "shift__shift_code",
    )

    list_filter = (
        "requirement_date",
        "shift",
    )

    autocomplete_fields = ("shift",)


# ============================================================
# LEAVE REQUEST ADMIN
# ============================================================

@admin.register(LeaveRequest)
class LeaveRequestAdmin(admin.ModelAdmin):

    list_display = (
        "employee",
        "start_date",
        "end_date",
        "status",
        "created_at",
        "reviewed_at",
    )

    search_fields = (
        "employee__employee_id",
        "employee__full_name",
        "reason",
    )

    list_filter = (
        "status",
        "start_date",
        "created_at",
    )

    readonly_fields = (
        "created_at",
        "reviewed_at",
    )

    autocomplete_fields = ("employee",)


# ============================================================
# ATTENDANCE ADMIN
# ============================================================

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):

    list_display = (
        "get_employee",
        "get_shift",
        "get_date",
        "status",
        "check_in",
        "check_out",
    )

    search_fields = (
        "assignment__employee__employee_id",
        "assignment__employee__full_name",
        "assignment__shift__shift_name",
    )

    list_filter = (
        "status",
        "assignment__shift_date",
    )

    readonly_fields = (
        "created_at",
        "updated_at",
    )

    @admin.display(description="Employee")
    def get_employee(self, obj):
        return obj.assignment.employee.full_name

    @admin.display(description="Shift")
    def get_shift(self, obj):
        return obj.assignment.shift.shift_name

    @admin.display(description="Date")
    def get_date(self, obj):
        return obj.assignment.shift_date
