from datetime import date, time

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import (
    Brand,
    BrandProcess,
    Employee,
    EmployeeAllocation,
    LeaveRequest,
    Pod,
    Process,
    PublicHoliday,
    Shift,
    StaffingRequirement,
    WeeklyOff,
)

ROSTER_DATE = date(2026, 12, 7)

ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]
NO_SUNDAY = [0, 1, 2, 3, 4, 5]

BRANDS = {
    "GLOW": "Glow Skincare",
    "URBN": "Urban Threads",
    "SPIC": "Spice Route",
    "PETP": "Pet Pals",
    "HOME": "Home Nest",
    "FITF": "Fit Fuel",
}

PROCESSES = {
    "CS": "Customer Support",
    "ACC": "Abandoned Cart Conversions",
    "RET": "Retention",
    "NDR": "Non-Delivery Report",
}

PODS = {
    "ALPHA": "Pod Alpha",
    "BETA": "Pod Beta",
    "GAMMA": "Pod Gamma",
    "DELTA": "Pod Delta",
}

# "BRAND-PROCESS": (working days, holiday policy, minimum staffing)
BRAND_PROCESS_RULES = {
    "GLOW-CS": (ALL_DAYS, "WORK", 2),
    "GLOW-ACC": (ALL_DAYS, "WORK", 1),
    "URBN-CS": (ALL_DAYS, "WORK", 1),
    "SPIC-CS": (ALL_DAYS, "WORK", 1),
    "SPIC-NDR": (NO_SUNDAY, "OFF", 1),
    "PETP-CS": (NO_SUNDAY, "OFF", 1),
    "PETP-RET": (NO_SUNDAY, "OFF", 1),
    "HOME-CS": (NO_SUNDAY, "OFF", 1),
    "FITF-CS": (ALL_DAYS, "WORK", 2),
    "FITF-ACC": (NO_SUNDAY, "OFF", 1),
    "FITF-RET": (NO_SUNDAY, "OFF", 1),
}

# (full name, brand-process keys, pod code)
EMPLOYEES = [
    ("Aarav Mehta", ["GLOW-CS"], "ALPHA"),
    ("Diya Sharma", ["GLOW-CS"], "ALPHA"),
    ("Rohan Iyer", ["GLOW-ACC"], "ALPHA"),
    ("Ananya Patil", ["URBN-CS"], "BETA"),
    ("Kabir Joshi", ["SPIC-CS"], "BETA"),
    ("Meera Nair", ["SPIC-NDR"], "BETA"),
    ("Vikram Rao", ["PETP-CS"], "GAMMA"),
    ("Sneha Kulkarni", ["PETP-RET"], "GAMMA"),
    ("Arjun Desai", ["HOME-CS"], "GAMMA"),
    ("Isha Verma", ["FITF-CS"], "DELTA"),
    ("Yash Pandey", ["FITF-ACC"], "DELTA"),
    ("Tanvi Shah", ["FITF-RET"], "DELTA"),
    ("Nikhil Gupta", ["GLOW-CS"], "ALPHA"),
    ("Pooja Menon", ["SPIC-CS"], "BETA"),
    ("Siddharth Roy", ["FITF-CS"], "DELTA"),
    ("Riya Kapoor", ["GLOW-ACC"], "ALPHA"),
    ("Karan Malhotra", ["PETP-CS"], "GAMMA"),
    ("Neha Bhatia", ["HOME-CS"], "GAMMA"),
    ("Aditya Kulshreshtha", ["FITF-RET"], "DELTA"),
    ("Farah Khan", ["SPIC-NDR"], "BETA"),
    ("Ishaan Saxena", ["GLOW-CS", "FITF-ACC"], "ALPHA"),
    ("Mira Dsouza", ["PETP-RET", "SPIC-CS"], "GAMMA"),
    ("Dev Thakur", ["URBN-CS"], "BETA"),
    ("Ritika Singh", ["HOME-CS"], "GAMMA"),
    ("Omkar Pawar", ["FITF-CS"], "DELTA"),
    ("Zoya Ansari", ["GLOW-ACC"], "ALPHA"),
    ("Harsh Vora", ["SPIC-NDR"], "BETA"),
    ("Kavya Reddy", ["PETP-CS"], "GAMMA"),
    ("Lakshay Bansal", ["FITF-RET"], "DELTA"),
    ("Simran Kaur", ["URBN-CS"], "BETA"),
]


class Command(BaseCommand):

    help = "Load a sample dataset: 30 employees, 6 brands, 4 processes, 4 pods."

    @transaction.atomic
    def handle(self, *args, **options):

        brands = {}
        for code, name in BRANDS.items():
            brands[code], _ = Brand.objects.get_or_create(
                code=code,
                defaults={"name": name},
            )

        processes = {}
        for code, name in PROCESSES.items():
            processes[code], _ = Process.objects.get_or_create(
                code=code,
                defaults={"name": name},
            )

        pods = {}
        for code, name in PODS.items():
            pods[code], _ = Pod.objects.get_or_create(
                code=code,
                defaults={"name": name},
            )

        brand_processes = {}
        for key, (working_days, holiday_policy, minimum) in BRAND_PROCESS_RULES.items():
            brand_code, process_code = key.split("-")
            brand_processes[key], _ = BrandProcess.objects.update_or_create(
                brand=brands[brand_code],
                process=processes[process_code],
                defaults={
                    "working_days": working_days,
                    "holiday_policy": holiday_policy,
                    "minimum_staffing": minimum,
                },
            )

        employees = []
        for number, (full_name, bp_keys, pod_code) in enumerate(EMPLOYEES, start=1):
            first_brand, first_process = bp_keys[0].split("-")

            employee, _ = Employee.objects.get_or_create(
                employee_id=f"DS{number:03d}",
                defaults={
                    "full_name": full_name,
                    "email": full_name.lower().replace(" ", ".") + "@example.com",
                    "phone": f"98000{number:05d}",
                    "brand": brands[first_brand].name,
                    "process": processes[first_process].name,
                    "joining_date": date(2026, 1, 1),
                },
            )
            employees.append(employee)

            for bp_key in bp_keys:
                EmployeeAllocation.objects.get_or_create(
                    employee=employee,
                    brand_process=brand_processes[bp_key],
                    defaults={
                        "pod": pods[pod_code],
                        "allocation_start": date(2026, 1, 1),
                    },
                )

            # Every 4th employee has a Sunday weekly off.
            if number % 4 == 0:
                WeeklyOff.objects.get_or_create(
                    employee=employee,
                    weekday=6,
                    effective_from=date(2026, 1, 1),
                )

        # Pod lead is the first employee listed in each pod.
        for pod_code, pod in pods.items():
            pod.lead = next(
                employee
                for employee, row in zip(employees, EMPLOYEES)
                if row[2] == pod_code
            )
            pod.save()

        shift, _ = Shift.objects.get_or_create(
            shift_code="MOR",
            defaults={
                "shift_name": "Morning Shift",
                "shift_type": "MORNING",
                "start_time": time(9, 0),
                "end_time": time(18, 0),
                "break_duration": 60,
                "is_active": True,
            },
        )

        for bp in brand_processes.values():
            StaffingRequirement.objects.update_or_create(
                shift=shift,
                brand_process=bp,
                requirement_date=ROSTER_DATE,
                defaults={"required_employees": bp.minimum_staffing},
            )

        # Ananya Patil (URBN-CS) takes approved leave on the roster date.
        LeaveRequest.objects.get_or_create(
            employee=employees[3],
            start_date=ROSTER_DATE,
            end_date=ROSTER_DATE,
            defaults={"reason": "Planned leave", "status": "APPROVED"},
        )

        PublicHoliday.objects.get_or_create(
            holiday_date=date(2026, 12, 25),
            region="IN",
            defaults={"name": "Christmas Day"},
        )

        self.stdout.write(self.style.SUCCESS(
            f"Sample data loaded: {Employee.objects.count()} employees, "
            f"{Brand.objects.count()} brands, {Process.objects.count()} processes, "
            f"{Pod.objects.count()} pods. Roster date: {ROSTER_DATE}."
        ))