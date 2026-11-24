import calendar
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

ROSTER_YEAR = 2026
ROSTER_MONTH = 12
DEMO_DATE = date(2026, 12, 7)

ALL_DAYS = [0, 1, 2, 3, 4, 5, 6]
NO_SUNDAY = [0, 1, 2, 3, 4, 5]

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

BRAND_NAMES = [
    "Glow Skincare", "Urban Threads", "Spice Route", "Pet Pals",
    "Home Nest", "Fit Fuel", "Bloom Beauty", "Peak Gear",
    "Cozy Kitchen", "Nova Audio", "Tiny Steps", "Silk and Stone",
    "Trail Mix Co", "Brew Lane", "Velvet Home", "Pixel Books",
    "Green Basket", "Urban Ink", "Sole Stride", "Mango Tea",
    "Riverside Decor", "Hue Paints", "Clear Lens", "Little Sprout",
]

EMPLOYEE_NAMES = [
    "Aarav Mehta", "Diya Sharma", "Rohan Iyer", "Ananya Patil",
    "Kabir Joshi", "Meera Nair", "Vikram Rao", "Sneha Kulkarni",
    "Arjun Desai", "Isha Verma", "Yash Pandey", "Tanvi Shah",
    "Nikhil Gupta", "Pooja Menon", "Siddharth Roy", "Riya Kapoor",
    "Karan Malhotra", "Neha Bhatia", "Aditya Kulshreshtha", "Farah Khan",
    "Ishaan Saxena", "Mira Dsouza", "Dev Thakur", "Ritika Singh",
    "Omkar Pawar", "Zoya Ansari", "Harsh Vora", "Kavya Reddy",
    "Lakshay Bansal", "Simran Kaur",
]

# Brands B01-B19 have one dedicated employee and one process each.
SINGLE_PROCESSES = ["CS", "ACC", "RET", "NDR"]
SINGLE_PATTERNS = [(ALL_DAYS, "WORK"), (ALL_DAYS, "OFF"), (NO_SUNDAY, "OFF")]

# Brands B20-B24 have several employees, split by process.
MULTI_BRAND_LAYOUTS = [
    {"CS": 1, "ACC": 1},
    {"CS": 1, "ACC": 1},
    {"CS": 1, "ACC": 1},
    {"CS": 1, "ACC": 1},
    {"CS": 2, "ACC": 1},
]


def build_plan():
    bp_specs = {}
    employee_specs = []

    for i in range(1, 20):
        brand_code = f"B{i:02d}"
        process_code = SINGLE_PROCESSES[(i - 1) % 4]
        working_days, holiday_policy = SINGLE_PATTERNS[(i - 1) % 3]
        key = f"{brand_code}-{process_code}"

        bp_specs[key] = {
            "working_days": working_days,
            "holiday_policy": holiday_policy,
            "minimum": 1,
        }
        employee_specs.append({"keys": [key]})

    for offset, layout in enumerate(MULTI_BRAND_LAYOUTS):
        brand_code = f"B{20 + offset:02d}"

        for process_code, count in layout.items():
            key = f"{brand_code}-{process_code}"

            bp_specs[key] = {
                "working_days": ALL_DAYS,
                "holiday_policy": "WORK",
                "minimum": count,
            }

            for _ in range(count):
                employee_specs.append({"keys": [key]})

    return bp_specs, employee_specs


BP_SPECS, EMPLOYEE_SPECS = build_plan()


class Command(BaseCommand):

    help = "Load sample data: 24 brands, 30 employees, 4 processes, 4 pods, December 2026 requirements."

    @transaction.atomic
    def handle(self, *args, **options):

        if len(EMPLOYEE_SPECS) != len(EMPLOYEE_NAMES):
            raise ValueError("Employee names and employee specs do not match.")

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

        brands = {}
        for index, name in enumerate(BRAND_NAMES, start=1):
            code = f"B{index:02d}"
            brands[code], _ = Brand.objects.get_or_create(
                code=code,
                defaults={"name": name},
            )

        brand_processes = {}
        for key, spec in BP_SPECS.items():
            brand_code, process_code = key.split("-")
            brand_processes[key], _ = BrandProcess.objects.update_or_create(
                brand=brands[brand_code],
                process=processes[process_code],
                defaults={
                    "working_days": spec["working_days"],
                    "holiday_policy": spec["holiday_policy"],
                    "minimum_staffing": spec["minimum"],
                },
            )

        pod_codes = list(PODS)
        employees = []

        for number, spec in enumerate(EMPLOYEE_SPECS, start=1):
            full_name = EMPLOYEE_NAMES[number - 1]
            first_brand, first_process = spec["keys"][0].split("-")

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

            for key in spec["keys"]:
                EmployeeAllocation.objects.get_or_create(
                    employee=employee,
                    brand_process=brand_processes[key],
                    defaults={
                        "pod": pods[pod_codes[(number - 1) % len(pod_codes)]],
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

        # The first four employees become the pod leads.
        for index, pod_code in enumerate(pod_codes):
            pod = pods[pod_code]
            pod.lead = employees[index]
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

        days = calendar.monthrange(ROSTER_YEAR, ROSTER_MONTH)[1]

        for day in range(1, days + 1):
            roster_day = date(ROSTER_YEAR, ROSTER_MONTH, day)

            for brand_process in brand_processes.values():
                StaffingRequirement.objects.update_or_create(
                    shift=shift,
                    brand_process=brand_process,
                    requirement_date=roster_day,
                    defaults={"required_employees": brand_process.minimum_staffing},
                )

        # DS001 (single-resource brand B01) is on approved leave on the demo date.
        LeaveRequest.objects.get_or_create(
            employee=employees[0],
            start_date=DEMO_DATE,
            end_date=DEMO_DATE,
            defaults={"reason": "Planned leave", "status": "APPROVED"},
        )

        PublicHoliday.objects.get_or_create(
            holiday_date=date(2026, 12, 31),
            region="IN",
            defaults={"name": "New Year's Eve"},
        )

        self.stdout.write(self.style.SUCCESS(
            f"Sample data loaded: {Employee.objects.count()} employees, "
            f"{Brand.objects.count()} brands, {Process.objects.count()} processes, "
            f"{Pod.objects.count()} pods, {BrandProcess.objects.count()} brand-processes. "
            f"Requirements created for {days} days of {ROSTER_MONTH}/{ROSTER_YEAR}."
        ))