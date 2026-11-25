# DataStraw Smart Roster

**A Full-Stack Employee Shift Scheduling and Roster Management System**

## Introduction
DataStraw Smart Roster plans and validates monthly rosters for an operations team that runs several D2C brands, each with its own processes, working days, and coverage rules. It separates each brand's operating calendar from individual employee schedules, generates rosters that respect weekly offs, leave, comp-offs, and public holidays, and reports shortages and conflicts instead of producing an invalid roster.
and roster management application designed to simplify workforce planning and improve scheduling efficiency.

The application provides a centralized platform where administrators can manage employee information, create and organize shift assignments, handle leave requests, and maintain employee schedules.

It combines a Django REST Framework backend with a React frontend to deliver a responsive and user-friendly experience.

## Features

- Employee management
- Automatic roster generation
- Employee shift scheduling
- Manual roster management
- Leave management
- REST API integration
- Database management
- Responsive user interface

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | React, JavaScript, CSS |
| Backend | Python, Django |
| API | Django REST Framework |
| Database | SQLite |
| Testing | Django Test Framework |
| Version Control | Git, GitHub |

## Project Structure

```text
DataStrawRoster/
│
├── backend/
│   ├── config/
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/
│   ├── src/
│   ├── public/
│   └── package.json
│
├── .gitignore
└── README.md
```

## Installation and Setup

### 1. Clone Repository

```bash
git clone https://github.com/tauseem/DataStraw-Smart-Roster.git
cd DataStraw-Smart-Roster
```

### 2. Backend Setup

```bash
cd backend
python -m venv .venv
```

Activate virtual environment on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run database migrations:

```bash
python manage.py migrate
```

Start Django server:

```bash
python manage.py runserver
```

Backend server:

`http://127.0.0.1:8000/`

API base path:

`http://127.0.0.1:8000/api/`

Admin panel:

`http://127.0.0.1:8000/admin/`

### 3. Frontend Setup

Open another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend application:

`http://localhost:5173/`

## Backend Testing

Run the following command from the backend directory:

```bash
python manage.py test
```

Latest verified test results:

- Total tests: 18
- Passed: 18
- Failed: 0

## Learning Outcomes

This project demonstrates practical experience in:

- Full-stack web development
- Python and Django development
- REST API development
- React frontend integration
- Database operations
- Automated testing
- Git and GitHub version control

## Future Enhancements


- Advanced scheduling optimization
- Enhanced analytics and reporting
- Role-based access control
- Improved dashboard visualizations


## How the System Works

**Modelling.** Employees, brands, processes, and pods are separate models. `BrandProcess` is the operating unit: it holds the brand's working days, public holiday policy, and minimum staffing. `EmployeeAllocation` links an employee to one or more brand-processes and a pod. Weekly offs, leave, and comp-offs belong to the employee, so brand calendars and individual schedules are kept apart.

**Generation.** For a given date, the generator collects staffing requirements for brand-processes that operate that day, keeps existing assignments, fills remaining gaps from unassigned active employees who are allocated to that brand-process and not on a weekly off, leave, or comp-off, and then moves surplus staff from over-covered requirements to under-covered ones. Shifts with attendance are never moved.

**Constraints.** Coverage, availability, and allocation are checked for every assignment the generator creates or moves, and also for assignments already on the roster. A roster is reported as successful only when it has no shortages and no conflicts.

**Single-resource and multi-employee brands.** A single-resource brand has one allocated employee. If that person is unavailable, the generator reports a shortage for the brand-process and does not silently leave the gap. Multi-employee brands draw from a shared pool, and surplus staff can be rebalanced.

**Unavailable sole employee.** The shortage is listed with the required and assigned counts. The fix is to add a backup allocation for the brand-process, then regenerate. Existing assignments are preserved, so only the gap is filled.

**Conflicts and insufficient staffing.** Each problem is returned as a structured item (shortage or conflict) with the reason, so nothing is hidden. Mandatory constraints are coverage and availability. Preferences are not yet modelled.

**Automated vs. human.** The system generates rosters, detects conflicts, and applies rebalancing. A manager still reviews the shortages and decides whether to add backups or change assignments. There is no approval workflow yet.

**If the company doubled.** Move the public holiday region into configuration, add a draft and publish state with an approval step, replace the greedy assignment with an optimisation approach, and add query indexes on dates and allocations.

**With one more week.** Model preferred weekly offs separately from mandatory constraints, validate manual edits through the same checks as generated assignments, and add a change-impact view that shows which brands lose coverage when someone becomes unavailable.


## Assumptions

- A brand-process operates on the working days set on it (for example Monday to Saturday), and does not operate on Sundays or on public holidays when its holiday policy is OFF.
- Each employee works one shift per day, so an employee cannot cover two brand-processes on the same day.
- Weekly offs are mandatory unless marked as preferred. Leave and comp-offs are always mandatory.
- Coverage requirements are set per brand-process per date. The sample data uses a minimum of one or two employees per brand-process.
- Single-resource brands are the brands with one allocated employee, which is about 80% of the sample brands.
- The sample dataset covers December 2026 and uses 30 employees, 24 brands, 4 processes, and 4 pods.

## Developer
## Tell Us How You Think

**1. How did you model employees, brands, processes, pods, and their relationships?**
Brands, processes, and pods are separate models. A `BrandProcess` is the operating unit: it holds a brand's working days, public holiday policy, and minimum staffing. An `EmployeeAllocation` links an employee to one brand-process and a pod, so one employee can serve several brand-processes. Weekly offs, leave, and comp-offs belong to the employee, so the brand's operating calendar is kept separate from individual schedules.

**2. How does your system generate a roster and determine whether it satisfies the constraints?**
For a date, the generator collects requirements for brand-processes that operate that day, keeps existing assignments, fills gaps from active employees who are allocated to that brand-process and are not on a weekly off, leave, or comp-off, and then moves surplus staff to under-covered requirements. A roster is reported as successful only when it has no shortages and no conflicts. Existing assignments are also checked, so someone already rostered on leave is flagged.

**3. How did you handle single-resource brands and brands with several employees?**
Both use the same model. Single-resource brands have one allocated employee, so if that person is unavailable the shortage is reported with the required and assigned counts, and the candidate list explains why each allocated employee is unavailable. Multi-employee brands draw from a shared pool, and surplus staff can be rebalanced to under-covered requirements. Shifts with attendance are never moved.

**4. What happens when an employee manages all processes for a brand but is unavailable on a required working day?**
The generator reports a shortage for that brand-process, lists its allocated employees with their reasons, and returns the result as unsuccessful. The sample data demonstrates this: DS001 is the only employee for a single-resource brand and is on approved leave on 7 December 2026. The fix is to add a backup allocation for that brand-process and regenerate. Existing assignments are preserved, so only the gap is filled.

**5. How does your system handle conflicting requirements or insufficient staffing?**
Each issue is returned as a structured item. Mandatory constraints (weekly off, approved leave, comp-off, allocation, and one shift per employee per day) are hard rules and produce conflicts or are skipped. Preferred weekly offs are soft: coverage can override them, and every override is listed in the roster result. Shortages report the required and assigned counts, the allocated employees with the reason each is unavailable, and suggested backups drawn from active employees who are not yet allocated to that brand-process.


**6. Which parts did you automate, and which did you leave under human control? Why?**
The system generates rosters, detects conflicts, rebalances surplus staff, and produces the monthly coverage view. A manager still reviews shortages and decides on backups, manual edits, and approvals. I kept those decisions human because a backup choice depends on skills and context the data doesn't capture, and an automatic change could silently break another brand.

**7. If the company doubled its team and brand count, what would you change?**
I would move the public holiday region into configuration, add a draft and publish state with an approval step, replace the greedy assignment with an optimisation approach, and add database indexes on dates and allocations. Monthly generation would also run as a background job rather than a request.

**8. If you had one additional week, what would you improve first?**
I would model preferred weekly offs separately from mandatory constraints, so coverage takes priority as the assignment requires. Next, I would validate manual edits through the same checks as generated assignments, and add a change-impact view that shows which brands lose coverage when someone becomes unavailable.


## Known Limitations

- An employee can hold only one shift per day, so covering two processes on the same day is not supported.
- Each single-resource brand in the sample data handles one process, and the sample has no spare cover on those brands. Shortages are expected and are reported rather than hidden.
- Public holidays use a fixed region code (`IN`).
- There is no draft or publish state. Conflicts and shortages are shown before a roster is treated as final, but the system does not lock a roster.
- Backup suggestions list employees who are not allocated to the brand-process. A manager must add an allocation before that person can be assigned.
- The change demo is a sequence of actions (approve leave, regenerate, review backups), not a single button.
- The free hosting tier resets the database on restart, so the sample data reloads on each start.

**Tauseem Shaikh**

Python / Django Developer | Full-Stack Developer

- GitHub: https://github.com/tauseem
- LinkedIn: https://www.linkedin.com/in/tauseem-shaikh

---

*Developed as a practical full-stack software development project.*gitgitgi
