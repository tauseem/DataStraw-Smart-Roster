from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import serializers

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


# =========================================================
# EMPLOYEE SERIALIZER
# =========================================================

class EmployeeSerializer(serializers.ModelSerializer):

    class Meta:
        model = Employee
        fields = "__all__"


# =========================================================
# SHIFT SERIALIZER
# =========================================================

class ShiftSerializer(serializers.ModelSerializer):

    class Meta:
        model = Shift
        fields = "__all__"

    def validate(self, attrs):
        start_time = attrs.get(
            "start_time",
            getattr(self.instance, "start_time", None)
        )

        end_time = attrs.get(
            "end_time",
            getattr(self.instance, "end_time", None)
        )

        if start_time and end_time and start_time == end_time:
            raise serializers.ValidationError(
                "Shift start time and end time cannot be the same."
            )

        return attrs


# =========================================================
# SHIFT ASSIGNMENT SERIALIZER
# =========================================================

class ShiftAssignmentSerializer(serializers.ModelSerializer):

    employee_name = serializers.CharField(
        source="employee.full_name",
        read_only=True
    )

    employee_code = serializers.CharField(
        source="employee.employee_id",
        read_only=True
    )

    shift_name = serializers.CharField(
        source="shift.shift_name",
        read_only=True
    )

    brand_name = serializers.CharField(
        source="brand_process.brand.name",
        read_only=True,
        default=None
    )

    process_name = serializers.CharField(
        source="brand_process.process.name",
        read_only=True,
        default=None
    )

    class Meta:
        model = ShiftAssignment
        fields = "__all__"

    def validate(self, attrs):

        employee = attrs.get(
            "employee",
            getattr(self.instance, "employee", None)
        )

        shift = attrs.get(
            "shift",
            getattr(self.instance, "shift", None)
        )

        shift_date = attrs.get(
            "shift_date",
            getattr(self.instance, "shift_date", None)
        )

        brand_process = attrs.get(
            "brand_process",
            getattr(self.instance, "brand_process", None)
        )

        status = attrs.get(
            "status",
            getattr(self.instance, "status", "SCHEDULED")
        )

        if status == "CANCELLED":
            return attrs

        if employee and employee.employment_status != "ACTIVE":
            raise serializers.ValidationError(
                "Inactive employees cannot be assigned shifts."
            )

        if shift and not shift.is_active:
            raise serializers.ValidationError(
                "Inactive shifts cannot be assigned."
            )

        if not employee or not shift or not shift_date:
            return attrs

        # -------------------------------------------------
        # BRAND PROCESS VALIDATION
        # -------------------------------------------------

        if brand_process:

            if not brand_process.is_active:
                raise serializers.ValidationError(
                    "This brand-process allocation is inactive."
                )

            if not brand_process.brand.is_active:
                raise serializers.ValidationError(
                    "This brand is inactive."
                )

            if not brand_process.process.is_active:
                raise serializers.ValidationError(
                    "This process is inactive."
                )

            # Check whether the brand-process works on this day.
            working_days = brand_process.working_days or []

            if shift_date.weekday() not in working_days:
                raise serializers.ValidationError(
                    "This brand-process does not operate on this day."
                )

            # Check public holiday.
            public_holiday = PublicHoliday.objects.filter(
                holiday_date=shift_date,
                region="IN"
            ).exists()

            if (
                public_holiday
                and brand_process.holiday_policy == "OFF"
            ):
                raise serializers.ValidationError(
                    "This brand-process does not operate on public holidays."
                )

            # Check employee allocation for the assignment date.
            allocation_exists = EmployeeAllocation.objects.filter(
                employee=employee,
                brand_process=brand_process,
                is_active=True,
                allocation_start__lte=shift_date
            ).filter(
                Q(allocation_end__isnull=True)
                | Q(allocation_end__gte=shift_date)
            ).exists()

            if not allocation_exists:
                raise serializers.ValidationError(
                    "This employee is not allocated to the selected "
                    "brand-process on this date."
                )

        # -------------------------------------------------
        # WEEKLY OFF VALIDATION
        # -------------------------------------------------

        weekly_off = WeeklyOff.objects.filter(
            employee=employee,
            weekday=shift_date.weekday(),
            effective_from__lte=shift_date,
            is_preference=False,
            is_active=True
        ).filter(
            Q(effective_until__isnull=True)
            | Q(effective_until__gte=shift_date)
        ).exists()

        if weekly_off:
            raise serializers.ValidationError(
                "This employee has a weekly off on the selected date."
            )

        # -------------------------------------------------
        # COMP-OFF VALIDATION
        # -------------------------------------------------

        comp_off = CompOff.objects.filter(
            employee=employee,
            usable_on=shift_date,
            status="APPROVED"
        ).exists()

        if comp_off:
            raise serializers.ValidationError(
                "This employee has an approved comp-off on this date."
            )

        # -------------------------------------------------
        # APPROVED LEAVE VALIDATION
        # -------------------------------------------------

        approved_leave = LeaveRequest.objects.filter(
            employee=employee,
            status="APPROVED",
            start_date__lte=shift_date,
            end_date__gte=shift_date
        ).exists()

        if approved_leave:
            raise serializers.ValidationError(
                "This employee is on approved leave."
            )

        # -------------------------------------------------
        # OVERLAPPING SHIFT VALIDATION
        # -------------------------------------------------

        new_start = datetime.combine(
            shift_date,
            shift.start_time
        )

        new_end = datetime.combine(
            shift_date,
            shift.end_time
        )

        if new_end <= new_start:
            new_end += timedelta(days=1)

        check_dates = [
            shift_date - timedelta(days=1),
            shift_date,
            shift_date + timedelta(days=1)
        ]

        existing_assignments = ShiftAssignment.objects.filter(
            employee=employee,
            shift_date__in=check_dates
        ).exclude(
            status="CANCELLED"
        )

        if self.instance:
            existing_assignments = existing_assignments.exclude(
                pk=self.instance.pk
            )

        for assignment in existing_assignments.select_related("shift"):

            existing_start = datetime.combine(
                assignment.shift_date,
                assignment.shift.start_time
            )

            existing_end = datetime.combine(
                assignment.shift_date,
                assignment.shift.end_time
            )

            if existing_end <= existing_start:
                existing_end += timedelta(days=1)

            overlaps = (
                new_start < existing_end
                and new_end > existing_start
            )

            if overlaps:
                raise serializers.ValidationError(
                    "This employee already has an overlapping shift."
                )

        return attrs


# =========================================================
# STAFFING REQUIREMENT SERIALIZER
# =========================================================

class StaffingRequirementSerializer(serializers.ModelSerializer):

    class Meta:
        model = StaffingRequirement
        fields = "__all__"

    def validate(self, attrs):

        required_employees = attrs.get(
            "required_employees",
            getattr(self.instance, "required_employees", None)
        )

        shift = attrs.get(
            "shift",
            getattr(self.instance, "shift", None)
        )

        brand_process = attrs.get(
            "brand_process",
            getattr(self.instance, "brand_process", None)
        )

        if (
            required_employees is not None
            and required_employees < 1
        ):
            raise serializers.ValidationError(
                "Required employees must be at least 1."
            )

        if shift and not shift.is_active:
            raise serializers.ValidationError(
                "Cannot create staffing requirements for inactive shifts."
            )

        if brand_process and not brand_process.is_active:
            raise serializers.ValidationError(
                "Cannot create staffing requirements for an inactive "
                "brand-process."
            )

        return attrs


# =========================================================
# LEAVE REQUEST SERIALIZER
# =========================================================

class LeaveRequestSerializer(serializers.ModelSerializer):

    employee_name = serializers.CharField(source="employee.full_name", read_only=True)
    employee_code = serializers.CharField(source="employee.employee_id", read_only=True)

    class Meta:
        model = LeaveRequest
        fields = "__all__"
        read_only_fields = (
            "created_at",
            "updated_at",
            "reviewed_at",
        )

    def validate(self, attrs):

        start_date = attrs.get(
            "start_date",
            getattr(self.instance, "start_date", None)
        )

        end_date = attrs.get(
            "end_date",
            getattr(self.instance, "end_date", None)
        )

        employee = attrs.get(
            "employee",
            getattr(self.instance, "employee", None)
        )

        if start_date and end_date and end_date < start_date:
            raise serializers.ValidationError(
                "End date cannot be before start date."
            )

        if employee and employee.employment_status != "ACTIVE":
            raise serializers.ValidationError(
                "Inactive employees cannot request leave."
            )

        if employee and start_date and end_date:

            overlapping_leaves = LeaveRequest.objects.filter(
                employee=employee,
                status__in=["PENDING", "APPROVED"],
                start_date__lte=end_date,
                end_date__gte=start_date
            )

            if self.instance:
                overlapping_leaves = overlapping_leaves.exclude(
                    pk=self.instance.pk
                )

            if overlapping_leaves.exists():
                raise serializers.ValidationError(
                    "An overlapping pending or approved leave already exists."
                )

        return attrs

    def update(self, instance, validated_data):

        new_status = validated_data.get(
            "status",
            instance.status
        )

        if new_status in ["APPROVED", "REJECTED"]:
            validated_data["reviewed_at"] = timezone.now()

        return super().update(instance, validated_data)


# =========================================================
# ATTENDANCE SERIALIZER
# =========================================================

class AttendanceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Attendance
        fields = "__all__"

    def validate(self, attrs):

        check_in = attrs.get(
            "check_in",
            getattr(self.instance, "check_in", None)
        )

        check_out = attrs.get(
            "check_out",
            getattr(self.instance, "check_out", None)
        )

        assignment = attrs.get(
            "assignment",
            getattr(self.instance, "assignment", None)
        )

        if check_in and check_out and check_out <= check_in:
            raise serializers.ValidationError(
                "Check-out time must be after check-in time."
            )

        if (
            assignment
            and assignment.status == "CANCELLED"
        ):
            raise serializers.ValidationError(
                "Attendance cannot be recorded for a cancelled assignment."
            )

        return attrs


# =========================================================
# BRAND SERIALIZER
# =========================================================

class BrandSerializer(serializers.ModelSerializer):

    class Meta:
        model = Brand
        fields = "__all__"


# =========================================================
# PROCESS SERIALIZER
# =========================================================

class ProcessSerializer(serializers.ModelSerializer):

    class Meta:
        model = Process
        fields = "__all__"


# =========================================================
# POD SERIALIZER
# =========================================================

class PodSerializer(serializers.ModelSerializer):

    class Meta:
        model = Pod
        fields = "__all__"


# =========================================================
# BRAND PROCESS SERIALIZER
# =========================================================

class BrandProcessSerializer(serializers.ModelSerializer):

    class Meta:
        model = BrandProcess
        fields = "__all__"

    def validate(self, attrs):

        working_days = attrs.get(
            "working_days",
            getattr(self.instance, "working_days", [])
        )

        minimum_staffing = attrs.get(
            "minimum_staffing",
            getattr(self.instance, "minimum_staffing", 1)
        )

        if not isinstance(working_days, list):
            raise serializers.ValidationError(
                "Working days must be a list."
            )

        for day in working_days:
            if (
                isinstance(day, bool)
                or not isinstance(day, int)
                or day < 0
                or day > 6
            ):
                raise serializers.ValidationError(
                    "Working days must contain integers from 0 to 6."
                )

        if minimum_staffing < 1:
            raise serializers.ValidationError(
                "Minimum staffing must be at least 1."
            )

        return attrs


# =========================================================
# EMPLOYEE ALLOCATION SERIALIZER
# =========================================================

class EmployeeAllocationSerializer(serializers.ModelSerializer):

    class Meta:
        model = EmployeeAllocation
        fields = "__all__"

    def validate(self, attrs):

        allocation_start = attrs.get(
            "allocation_start",
            getattr(self.instance, "allocation_start", None)
        )

        allocation_end = attrs.get(
            "allocation_end",
            getattr(self.instance, "allocation_end", None)
        )

        employee = attrs.get(
            "employee",
            getattr(self.instance, "employee", None)
        )

        brand_process = attrs.get(
            "brand_process",
            getattr(self.instance, "brand_process", None)
        )

        if (
            allocation_start
            and allocation_end
            and allocation_end < allocation_start
        ):
            raise serializers.ValidationError(
                "Allocation end date cannot be before start date."
            )

        if employee and employee.employment_status != "ACTIVE":
            raise serializers.ValidationError(
                "Inactive employees cannot be allocated."
            )

        if brand_process and not brand_process.is_active:
            raise serializers.ValidationError(
                "Employees cannot be allocated to an inactive brand-process."
            )

        return attrs


# =========================================================
# PUBLIC HOLIDAY SERIALIZER
# =========================================================

class PublicHolidaySerializer(serializers.ModelSerializer):

    class Meta:
        model = PublicHoliday
        fields = "__all__"


# =========================================================
# WEEKLY OFF SERIALIZER
# =========================================================

class WeeklyOffSerializer(serializers.ModelSerializer):

    class Meta:
        model = WeeklyOff
        fields = "__all__"

    def validate(self, attrs):

        effective_from = attrs.get(
            "effective_from",
            getattr(self.instance, "effective_from", None)
        )

        effective_until = attrs.get(
            "effective_until",
            getattr(self.instance, "effective_until", None)
        )

        if (
            effective_from
            and effective_until
            and effective_until < effective_from
        ):
            raise serializers.ValidationError(
                "Effective until date cannot be before effective from date."
            )

        return attrs


# =========================================================
# COMP-OFF SERIALIZER
# =========================================================

class CompOffSerializer(serializers.ModelSerializer):

    class Meta:
        model = CompOff
        fields = "__all__"


# =========================================================
# COVERAGE REQUIREMENT SERIALIZER
# =========================================================

class CoverageRequirementSerializer(serializers.ModelSerializer):

    class Meta:
        model = CoverageRequirement
        fields = "__all__"

    def validate(self, attrs):

        required_employees = attrs.get(
            "required_employees",
            getattr(self.instance, "required_employees", None)
        )

        brand_process = attrs.get(
            "brand_process",
            getattr(self.instance, "brand_process", None)
        )

        if (
            required_employees is not None
            and required_employees < 1
        ):
            raise serializers.ValidationError(
                "Required employees must be at least 1."
            )

        if brand_process and not brand_process.is_active:
            raise serializers.ValidationError(
                "Cannot create coverage requirements for an inactive "
                "brand-process."
            )

        return attrs