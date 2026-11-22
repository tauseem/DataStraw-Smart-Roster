from datetime import date, time

from django.test import TestCase
from rest_framework.test import APIClient

from .models import (
    Employee,
    Shift,
    ShiftAssignment,
    StaffingRequirement,
    LeaveRequest,
    Attendance,
    WeeklyOff,
    CompOff,
)


class SmartRosterAPITests(TestCase):

    def setUp(self):

        self.client = APIClient()

        self.employee = Employee.objects.create(
            employee_id="EMP001",
            full_name="Test Employee",
            email="testemployee@example.com",
            phone="9876543210",
            brand="Test Brand",
            process="Customer Support",
            employment_status="ACTIVE",
            joining_date=date(2026, 1, 1),
        )

        self.shift = Shift.objects.create(
            shift_name="Morning Shift",
            shift_code="MOR",
            shift_type="MORNING",
            start_time=time(9, 0),
            end_time=time(18, 0),
            break_duration=60,
            is_active=True,
        )

        self.roster_date = date(2026, 11, 12)


    # --------------------------------------------------
    # REBALANCING PROTECTION TEST HELPER
    # --------------------------------------------------

    
    def create_protection_scenario(self, protection):

        # Use the employee already created by setUp().
        employees = [self.employee]

        # Create only ONE additional employee.
        second_employee = Employee.objects.create(
            employee_id="PROT002",
            full_name="Protected Employee 2",
            email="protected2@example.com",
            phone="9876543211",
            brand="Test Brand",
            process="Customer Support",
            employment_status="ACTIVE",
            joining_date=date(2026, 1, 1),
        )

        employees.append(second_employee)

        evening_shift = Shift.objects.create(
            shift_name="Protection Evening",
            shift_code="PEV",
            shift_type="GENERAL",
            start_time=time(18, 0),
            end_time=time(23, 0),
            break_duration=30,
            is_active=True,
        )

        StaffingRequirement.objects.create(
            shift=self.shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        StaffingRequirement.objects.create(
            shift=evening_shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        assignments = []

        for employee in employees:

            assignment = ShiftAssignment.objects.create(
                employee=employee,
                shift=evening_shift,
                shift_date=self.roster_date,
                status="SCHEDULED",
            )

            assignments.append(assignment)

            if protection == "leave":

                LeaveRequest.objects.create(
                    employee=employee,
                    start_date=self.roster_date,
                    end_date=self.roster_date,
                    reason="Approved leave",
                    status="APPROVED",
                )

            elif protection == "weekly_off":

                WeeklyOff.objects.create(
                    employee=employee,
                    weekday=self.roster_date.weekday(),
                    effective_from=self.roster_date,
                    is_active=True,
                )

            elif protection == "comp_off":

                CompOff.objects.create(
                    employee=employee,
                    earned_on=date(2026, 11, 1),
                    usable_on=self.roster_date,
                    status="APPROVED",
                )

            elif protection == "attendance":

                Attendance.objects.create(
                    assignment=assignment,
                    status="PRESENT",
                )

        return evening_shift, assignments

    # --------------------------------------------------
    # APPROVED COMP-OFF PROTECTION
    # --------------------------------------------------

    def test_rebalancing_does_not_move_employees_on_comp_off(self):

        evening_shift, assignments = (
            self.create_protection_scenario("comp_off")
        )

        response = self.client.post(
            "/api/generate-roster/",
            {"date": str(self.roster_date)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["rebalanced_count"],
            0,
        )

        self.assertEqual(
            response.data["shortages"][0]["shortage"],
            1,
        )

        for assignment in assignments:
            assignment.refresh_from_db()
            self.assertEqual(assignment.shift_id, evening_shift.id)

    # --------------------------------------------------
    # ATTENDANCE PROTECTION
    # --------------------------------------------------

    def test_rebalancing_does_not_move_employees_with_attendance(self):

        evening_shift, assignments = (
            self.create_protection_scenario("attendance")
        )

        response = self.client.post(
            "/api/generate-roster/",
            {"date": str(self.roster_date)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["rebalanced_count"],
            0,
        )

        self.assertEqual(
            response.data["shortages"][0]["shortage"],
            1,
        )

        for assignment in assignments:
            assignment.refresh_from_db()
            self.assertEqual(assignment.shift_id, evening_shift.id)



    # --------------------------------------------------
    # APPROVED LEAVE PROTECTION
    # --------------------------------------------------

    def test_rebalancing_does_not_move_employees_on_approved_leave(self):

        evening_shift, assignments = (
            self.create_protection_scenario("leave")
        )

        response = self.client.post(
            "/api/generate-roster/",
            {"date": str(self.roster_date)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["rebalanced_count"],
            0,
        )

        self.assertEqual(
            response.data["shortages"][0]["shortage"],
            1,
        )

        for assignment in assignments:
            assignment.refresh_from_db()
            self.assertEqual(assignment.shift_id, evening_shift.id)

    # --------------------------------------------------
    # WEEKLY OFF PROTECTION
    # --------------------------------------------------

    def test_rebalancing_does_not_move_employees_on_weekly_off(self):

        evening_shift, assignments = (
            self.create_protection_scenario("weekly_off")
        )

        response = self.client.post(
            "/api/generate-roster/",
            {"date": str(self.roster_date)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["rebalanced_count"],
            0,
        )

        self.assertEqual(
            response.data["shortages"][0]["shortage"],
            1,
        )

        for assignment in assignments:
            assignment.refresh_from_db()
            self.assertEqual(assignment.shift_id, evening_shift.id)

    # --------------------------------------------------
    # AUTOMATIC SHIFT REBALANCING
    # --------------------------------------------------

    def test_roster_rebalances_overstaffed_shift(self):

        second_employee = Employee.objects.create(
            employee_id="EMP002",
            full_name="Second Employee",
            email="secondemployee@example.com",
            phone="9876543211",
            brand="Test Brand",
            process="Customer Support",
            employment_status="ACTIVE",
            joining_date=date(2026, 1, 1),
        )

        evening_shift = Shift.objects.create(
            shift_name="Evening Shift",
            shift_code="EVE",
            shift_type="GENERAL",
            start_time=time(18, 0),
            end_time=time(23, 0),
            break_duration=30,
            is_active=True,
        )

        # Morning shift has one extra employee.
        StaffingRequirement.objects.create(
            shift=self.shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        # Evening shift needs one employee.
        StaffingRequirement.objects.create(
            shift=evening_shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        # Two employees are already assigned to Morning.
        ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.shift,
            shift_date=self.roster_date,
            status="SCHEDULED",
        )

        ShiftAssignment.objects.create(
            employee=second_employee,
            shift=self.shift,
            shift_date=self.roster_date,
            status="SCHEDULED",
        )

        response = self.client.post(
            "/api/generate-roster/",
            {
                "date": str(self.roster_date),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["rebalanced_count"],
            1,
        )

        self.assertEqual(
            ShiftAssignment.objects.filter(
                shift=self.shift,
                shift_date=self.roster_date,
                status="SCHEDULED",
            ).count(),
            1,
        )

        self.assertEqual(
            ShiftAssignment.objects.filter(
                shift=evening_shift,
                shift_date=self.roster_date,
                status="SCHEDULED",
            ).count(),
            1,
        )

        self.assertEqual(
            response.data["shortages"],
            [],
        )


    # --------------------------------------------------
    # HEALTH CHECK
    # --------------------------------------------------

    def test_health_check(self):

        response = self.client.get("/api/health/")

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

    # --------------------------------------------------
    # EMPLOYEE API
    # --------------------------------------------------

    def test_employee_list(self):

        response = self.client.get("/api/employees/")

        self.assertEqual(response.status_code, 200)

    # --------------------------------------------------
    # SHIFT API
    # --------------------------------------------------

    def test_shift_list(self):

        response = self.client.get("/api/shifts/")

        self.assertEqual(response.status_code, 200)

    # --------------------------------------------------
    # STAFFING REQUIREMENT
    # --------------------------------------------------

    def test_create_staffing_requirement(self):

        requirement = StaffingRequirement.objects.create(
            shift=self.shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        self.assertEqual(
            requirement.required_employees,
            1
        )

    # --------------------------------------------------
    # ROSTER GENERATION
    # --------------------------------------------------

    def test_roster_generation(self):

        StaffingRequirement.objects.create(
            shift=self.shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        response = self.client.post(
            "/api/generate-roster/",
            {
                "date": str(self.roster_date),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["generated_count"],
            1
        )

        self.assertEqual(
            ShiftAssignment.objects.filter(
                shift_date=self.roster_date
            ).count(),
            1
        )

    # --------------------------------------------------
    # EXISTING ASSIGNMENTS ARE PRESERVED
    # --------------------------------------------------

    def test_existing_assignment_is_preserved(self):

        existing = ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.shift,
            shift_date=self.roster_date,
            status="SCHEDULED",
        )

        StaffingRequirement.objects.create(
            shift=self.shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        response = self.client.post(
            "/api/generate-roster/",
            {
                "date": str(self.roster_date),
            },
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["generated_count"],
            0
        )

        self.assertTrue(
            ShiftAssignment.objects.filter(
                id=existing.id
            ).exists()
        )

    # --------------------------------------------------
    # LEAVE REQUEST
    # --------------------------------------------------

    def test_leave_request_creation(self):

        leave = LeaveRequest.objects.create(
            employee=self.employee,
            start_date=self.roster_date,
            end_date=self.roster_date,
            reason="Personal work",
            status="PENDING",
        )

        self.assertEqual(
            leave.status,
            "PENDING"
        )

    # --------------------------------------------------
    # ATTENDANCE
    # --------------------------------------------------

    def test_attendance_creation(self):

        assignment = ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.shift,
            shift_date=self.roster_date,
            status="SCHEDULED",
        )

        attendance = Attendance.objects.create(
            assignment=assignment,
            status="PRESENT",
        )

        self.assertEqual(
            attendance.status,
            "PRESENT"
        )

    # --------------------------------------------------
    # DASHBOARD SUMMARY
    # --------------------------------------------------

    def test_dashboard_summary(self):

        response = self.client.get(
            "/api/dashboard-summary/"
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.data["success"])

    # --------------------------------------------------
    # ROSTER CALENDAR
    # --------------------------------------------------

    def test_roster_calendar(self):

        ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.shift,
            shift_date=self.roster_date,
            status="SCHEDULED",
        )

        response = self.client.get(
            "/api/roster-calendar/",
            {
                "date": str(self.roster_date),
            },
        )

        self.assertEqual(response.status_code, 200)

        self.assertEqual(
            response.data["count"],
            1
        )



    # --------------------------------------------------
    # CONFLICT: ASSIGNED EMPLOYEE ON APPROVED LEAVE
    # --------------------------------------------------

    def test_existing_assignment_on_approved_leave_is_flagged(self):

        LeaveRequest.objects.create(
            employee=self.employee,
            start_date=self.roster_date,
            end_date=self.roster_date,
            reason="Approved leave",
            status="APPROVED",
        )

        ShiftAssignment.objects.create(
            employee=self.employee,
            shift=self.shift,
            shift_date=self.roster_date,
            status="SCHEDULED",
        )

        StaffingRequirement.objects.create(
            shift=self.shift,
            requirement_date=self.roster_date,
            required_employees=1,
        )

        response = self.client.post(
            "/api/generate-roster/",
            {"date": str(self.roster_date)},
            format="json",
        )

        self.assertEqual(response.status_code, 200)

        self.assertIn("conflicts", response.data)

        self.assertEqual(len(response.data["conflicts"]), 1)

        self.assertEqual(
            response.data["conflicts"][0]["employee_id"],
            "EMP001",
        )

        self.assertEqual(
            response.data["conflicts"][0]["reason"],
            "Approved leave",
        )