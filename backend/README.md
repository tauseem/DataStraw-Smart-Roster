# DataStraw Smart Roster

A full-stack employee scheduling and workforce management application built with Django REST Framework and React.

DataStraw Smart Roster provides tools for managing employees, shifts, roster assignments, staffing requirements, leave requests, attendance, and workforce allocation through a web-based interface.

## Features

- Employee management
- Shift management
- Shift assignment management
- Staffing requirements
- Leave request management
- Attendance management
- Brand, process, and pod management
- Employee allocation management
- Public holiday and weekly-off management
- Comp-off management
- Coverage requirements
- Roster generation API
- Roster calendar API
- Dashboard summary API
- Backend automated tests

## Technology Stack

### Backend
- Python
- Django 6.1.3
- Django REST Framework 3.18.3
- SQLite
- django-cors-headers

### Frontend
- React 19
- Vite 8
- JavaScript
- HTML5
- CSS3

## Project Structure

```text
DataStrawRoster/
│
├── backend/
│   ├── config/
│   ├── core/
│   ├── requirements.txt
│   └── manage.py
│
├── frontend/
│   ├── src/
│   ├── public/
│   ├── package.json
│   └── package-lock.json
│
├── .gitignore
└── README.md
```

## Getting Started

### Prerequisites

Install the following before running the project:

- Python
- Node.js and npm
- Git

### 1. Clone the repository

```bash
git clone https://github.com/tauseem/DataStraw-Smart-Roster.git
cd DataStrawRoster
```

### 2. Backend setup

Open a terminal in the project root:

```powershell
cd backend

python -m venv .venv

.\.venv\Scripts\Activate.ps1

pip install -r requirements.txt
```

### 3. Configure the Django secret key

Set a secret key as an environment variable. Do not commit your actual secret key to Git.

In PowerShell:

```powershell
$env:DJANGO_SECRET_KEY = "your-generated-secret-key"
```

For a persistent Windows user environment variable, configure it separately through Windows environment variables.

### 4. Run database migrations

```powershell
python manage.py migrate
```

### 5. Start the backend server

```powershell
python manage.py runserver
```

Backend development server:

`http://127.0.0.1:8000/`

### 6. Frontend setup

Open another terminal:

```powershell
cd frontend

npm ci

npm run dev
```

Frontend development server:

`http://localhost:5173/`

## API Endpoints

The backend exposes REST API endpoints for:

| Endpoint | Purpose |
|---|---|
| `/api/health/` | API health check |
| `/api/employees/` | Employee management |
| `/api/shifts/` | Shift management |
| `/api/assignments/` | Shift assignments |
| `/api/staffing-requirements/` | Staffing requirements |
| `/api/leave-requests/` | Leave requests |
| `/api/attendance/` | Attendance records |
| `/api/brands/` | Brand management |
| `/api/processes/` | Process management |
| `/api/pods/` | Pod management |
| `/api/brand-processes/` | Brand-process management |
| `/api/employee-allocations/` | Employee allocations |
| `/api/public-holidays/` | Public holidays |
| `/api/weekly-offs/` | Weekly offs |
| `/api/comp-offs/` | Comp-off records |
| `/api/coverage-requirements/` | Coverage requirements |
| `/api/generate-roster/` | Roster generation |
| `/api/roster-calendar/` | Roster calendar |
| `/api/dashboard-summary/` | Dashboard summary |

## Running Backend Tests

From the backend directory:

```powershell
python manage.py test
```

Run Django system checks:

```powershell
python manage.py check
```

## Frontend Validation

From the frontend directory:

Build the production frontend:

```powershell
npm run build
```

Run the linter:

```powershell
npm run lint
```

## Screenshots

Screenshots of the application will be added here to demonstrate the user interface and project functionality.

## Future Improvements

- Additional workforce scheduling capabilities
- Enhanced reporting and analytics
- Improved roster management workflows
- Further validation and automated testing

## Author

**Tauseem Shaikh**

GitHub: [tauseem](https://github.com/tauseem)

Repository: [DataStraw Smart Roster](https://github.com/tauseem/DataStraw-Smart-Roster)
