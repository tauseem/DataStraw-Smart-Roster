# DataStraw Smart Roster

**A Full-Stack Employee Shift Scheduling and Roster Management System**

## Introduction

DataStraw Smart Roster is a web-based employee shift scheduling and roster management application designed to simplify workforce planning and improve scheduling efficiency.

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

- Cloud deployment
- Advanced scheduling optimization
- Enhanced analytics and reporting
- Role-based access control
- Improved dashboard visualizations

## Developer

**Tauseem Shaikh**

Python / Django Developer | Full-Stack Developer

- GitHub: https://github.com/tauseem
- LinkedIn: https://www.linkedin.com/in/tauseem-shaikh

---

*Developed as a practical full-stack software development project.*gitgitgi
