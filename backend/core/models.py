
from django.db import models
from django.db.models import Q


# ============================================================
# COMMON DEFAULTS
# ============================================================

def default_working_days():
    # Monday=0, Tuesday=1 ... Sunday=6
    return [0, 1, 2, 3, 4, 5, 6]


WEEKDAY_CHOICES = [
    (0, "Monday"),
    (1, "Tuesday"),
    (2, "Wednesday"),
    (3, "Thursday"),
    (4, "Friday"),
    (5, "Saturday"),
    (6, "Sunday"),
]


# ============================================================
# EMPLOYEE
# ============================================================

class Employee(models.Model):

    EMPLOYMENT_STATUS = [
        ("ACTIVE", "Active"),
        ("INACTIVE", "Inactive"),
    ]

    employee_id = models.CharField(max_length=20, unique=True)
    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)

    # Legacy text fields.
    # New brand/process relationships use EmployeeAllocation.
    brand = models.CharField(max_length=100)
    process = models.CharField(max_length=100)

    employment_status = models.CharField(
        max_length=10,
        choices=EMPLOYMENT_STATUS,
        default="ACTIVE"
    )

    joining_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.employee_id} - {self.full_name}"


# ============================================================
# BRAND MANAGEMENT
# ============================================================

class Brand(models.Model):

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ============================================================
# PROCESS MANAGEMENT
# ============================================================

class Process(models.Model):

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ============================================================
# OPERATIONAL POD MANAGEMENT
# ============================================================

class Pod(models.Model):

    name = models.CharField(max_length=100, unique=True)
    code = models.CharField(max_length=30, unique=True)
    description = models.TextField(blank=True)

    lead = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="led_pods"
    )

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return f"{self.name} ({self.code})"


# ============================================================
# BRAND + PROCESS CONFIGURATION
# ============================================================

class BrandProcess(models.Model):

    HOLIDAY_POLICIES = [
        ("WORK", "Works on public holidays"),
        ("OFF", "Public holidays off"),
    ]

    brand = models.ForeignKey(
        Brand,
        on_delete=models.CASCADE,
        related_name="brand_processes"
    )

    process = models.ForeignKey(
        Process,
        on_delete=models.CASCADE,
        related_name="brand_processes"
    )

    working_days = models.JSONField(
        default=default_working_days
    )

    holiday_policy = models.CharField(
        max_length=10,
        choices=HOLIDAY_POLICIES,
        default="OFF"
    )

    minimum_staffing = models.PositiveIntegerField(default=1)
    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["brand__name", "process__name"]
        constraints = [
            models.UniqueConstraint(
                fields=["brand", "process"],
                name="unique_brand_process"
            )
        ]

    def __str__(self):
        return f"{self.brand.name} - {self.process.name}"


# ============================================================
# EMPLOYEE ALLOCATION
# ============================================================

class EmployeeAllocation(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="allocations"
    )

    brand_process = models.ForeignKey(
        BrandProcess,
        on_delete=models.CASCADE,
        related_name="employee_allocations"
    )

    pod = models.ForeignKey(
        Pod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="employee_allocations"
    )

    allocation_start = models.DateField()
    allocation_end = models.DateField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["employee__full_name"]
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "brand_process"],
                name="unique_employee_brand_process_allocation"
            )
        ]

    def __str__(self):
        return (
            f"{self.employee.full_name} - "
            f"{self.brand_process.brand.name} - "
            f"{self.brand_process.process.name}"
        )


# ============================================================
# PUBLIC HOLIDAYS
# ============================================================

class PublicHoliday(models.Model):

    name = models.CharField(max_length=100)
    holiday_date = models.DateField()

    region = models.CharField(
        max_length=50,
        default="IN"
    )

    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["holiday_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["holiday_date", "region"],
                name="unique_public_holiday_per_region"
            )
        ]

    def __str__(self):
        return f"{self.name} - {self.holiday_date}"


# ============================================================
# EMPLOYEE WEEKLY OFF
# ============================================================

class WeeklyOff(models.Model):

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="weekly_offs"
    )

    weekday = models.PositiveSmallIntegerField(
        choices=WEEKDAY_CHOICES
    )

    effective_from = models.DateField()
    effective_until = models.DateField(
        null=True,
        blank=True
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["employee__full_name", "weekday"]

    def __str__(self):
        return (
            f"{self.employee.full_name} - "
            f"{self.get_weekday_display()} off"
        )


# ============================================================
# COMPENSATORY OFF
# ============================================================

class CompOff(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
        ("USED", "Used"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="comp_offs"
    )

    earned_on = models.DateField()
    usable_on = models.DateField(
        null=True,
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    reason = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"{self.employee.full_name} - "
            f"Comp Off ({self.status})"
        )


# ============================================================
# DATE-SPECIFIC COVERAGE REQUIREMENTS
# ============================================================

class CoverageRequirement(models.Model):

    brand_process = models.ForeignKey(
        BrandProcess,
        on_delete=models.CASCADE,
        related_name="coverage_requirements"
    )

    requirement_date = models.DateField()
    required_employees = models.PositiveIntegerField(default=1)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["requirement_date"]
        constraints = [
            models.UniqueConstraint(
                fields=["brand_process", "requirement_date"],
                name="unique_brand_process_coverage_date"
            )
        ]

    def __str__(self):
        return (
            f"{self.brand_process} - "
            f"{self.requirement_date} - "
            f"{self.required_employees} employees"
        )


# ============================================================
# SHIFT MANAGEMENT
# ============================================================

class Shift(models.Model):

    SHIFT_TYPES = [
        ("MORNING", "Morning"),
        ("AFTERNOON", "Afternoon"),
        ("NIGHT", "Night"),
        ("GENERAL", "General"),
    ]

    shift_name = models.CharField(max_length=50)
    shift_code = models.CharField(max_length=20, unique=True)

    shift_type = models.CharField(
        max_length=20,
        choices=SHIFT_TYPES
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    break_duration = models.PositiveIntegerField(default=60)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.shift_name} ({self.shift_code})"


# ============================================================
# SHIFT ASSIGNMENTS
# ============================================================

class ShiftAssignment(models.Model):

    STATUS_CHOICES = [
        ("SCHEDULED", "Scheduled"),
        ("COMPLETED", "Completed"),
        ("CANCELLED", "Cancelled"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="shift_assignments"
    )

    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name="assignments"
    )

    # Records which brand/process this assignment belongs to.
    # Nullable to preserve existing assignments.
    brand_process = models.ForeignKey(
        BrandProcess,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="shift_assignments"
    )

    shift_date = models.DateField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="SCHEDULED"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["employee", "shift_date"],
                condition=~Q(status="CANCELLED"),
                name="unique_active_employee_shift_per_day"
            )
        ]

    def __str__(self):
        return (
            f"{self.employee.full_name} - "
            f"{self.shift.shift_name} - {self.shift_date}"
        )


# ============================================================
# SHIFT STAFFING REQUIREMENTS
# ============================================================

class StaffingRequirement(models.Model):

    shift = models.ForeignKey(
        Shift,
        on_delete=models.CASCADE,
        related_name="staffing_requirements"
    )

    # Optional brand/process connection.
    # NULL represents a legacy shift-only requirement.
    brand_process = models.ForeignKey(
        BrandProcess,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="staffing_requirements"
    )

    requirement_date = models.DateField()
    required_employees = models.PositiveIntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            # Only one legacy requirement without a brand/process
            # for a particular shift and date.
            models.UniqueConstraint(
                fields=["shift", "requirement_date"],
                condition=Q(brand_process__isnull=True),
                name="unique_legacy_shift_staffing_requirement"
            ),

            # Allow multiple brand/process requirements for the
            # same shift and date, but prevent duplicate combinations.
            models.UniqueConstraint(
                fields=[
                    "shift",
                    "brand_process",
                    "requirement_date"
                ],
                condition=Q(brand_process__isnull=False),
                name="unique_shift_brand_process_staffing_requirement"
            )
        ]

    def __str__(self):
        return (
            f"{self.shift.shift_name} - "
            f"{self.requirement_date} - "
            f"{self.required_employees} employees"
        )


# ============================================================
# LEAVE MANAGEMENT
# ============================================================

class LeaveRequest(models.Model):

    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("APPROVED", "Approved"),
        ("REJECTED", "Rejected"),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name="leave_requests"
    )

    start_date = models.DateField()
    end_date = models.DateField()
    reason = models.TextField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PENDING"
    )

    manager_comment = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return (
            f"{self.employee.full_name} - "
            f"{self.start_date} to {self.end_date} ({self.status})"
        )


# ============================================================
# ATTENDANCE
# ============================================================

class Attendance(models.Model):

    STATUS_CHOICES = [
        ("PRESENT", "Present"),
        ("ABSENT", "Absent"),
        ("LATE", "Late"),
        ("HALF_DAY", "Half Day"),
    ]

    assignment = models.OneToOneField(
        ShiftAssignment,
        on_delete=models.CASCADE,
        related_name="attendance"
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default="PRESENT"
    )

    check_in = models.DateTimeField(null=True, blank=True)
    check_out = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.assignment.employee.full_name} - "
            f"{self.assignment.shift_date} - {self.status}"
        )
