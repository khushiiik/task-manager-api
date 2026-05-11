# Task Manager API

A production-style Task Management System built with **Django REST Framework (DRF)** featuring role-based workflows, team management, async notifications, Redis caching, Celery background tasks, Dockerized services, and PostgreSQL integration.

This project simulates a real-world company workflow where Admins, Managers, Developers, and QA members collaborate through projects and tasks.

---

# 🚀 Features

# 🔐 Authentication & User Management

* JWT Authentication

* Access & Refresh Token support

* Custom User Model using `AbstractUser`

* Role-based user system

  * Admin
  * Manager
  * Developer
  * QA

* Admin-controlled user creation

* Public registration is disabled

* Admin provides username and temporary password to users

* Users login using admin-provided credentials

* Users can change their password after login

* Users cannot change:

  * role
  * team
  * username
  * email

* Secure password hashing

* Password change endpoint

* User profile endpoint

---

# 🔔 Notification System

Async notification system using Celery + Redis.

Notifications are automatically created when:

* a task gets assigned
* assignee changes

The notification system also supports manual messaging between users.

Users can:

* send custom notification messages
* select recipient users
* request help or approvals
* communicate workflow-related information

Features:

* User-specific notifications
* Manual notification sending
* Mark notification as read
* Background task processing
* Async notification delivery
* Notifications trigger automatically when task assignments change

---

# 👥 Team Management

* Team creation and management
* Team-member relationships
* One Manager per team
* One QA per team
* Team-based project organization

---

# 📁 Project Management

* Project CRUD APIs
* Active / Inactive project support
* Team-based project ownership
* Project creator tracking
* Project update tracking
* Start & end dates
* Redis caching for project endpoints

### Important Business Logic

* Inactive project tasks are hidden from normal team members
* Only Admins and Managers can access inactive project tasks

---

# ✅ Task Management

* Task CRUD APIs

* Team-scoped task visibility

* Cross-team task assignment (Admin-only)

* Task states:

  * Draft
  * In Progress
  * In Review
  * Completed
  * Blocked
  * Cancelled

* Task priority support

* Due date support

* Task creator tracking

* Last updated by tracking

* Admin users are excluded from task assignment

* Validation prevents assigning tasks to Admin users

---

# 🔍 Task Filtering

Supports filtering tasks by:

* State
* Priority
* Due date range
* Assigned to current user

### Example

```bash id="sgbrgn"
/tasks/?state=in_review
/tasks/?priority=true
/tasks/?assigned_to_me=true
/tasks/?deadline_before=2026-05-20
```

---

# ⚡ Async Processing with Celery

This project uses:

* Celery
* Redis

for:

* background notifications
* async task processing

---

# 📊 Reporting System

Raw SQL reporting endpoint included.

### Example Report

* Overdue tasks per user

Demonstrates:

* SQL joins
* grouping
* aggregation
* reporting queries

---

# 🔒 Permissions & Security

## Admin

Can:

* manage everything
* manage users
* manage teams
* assign cross-team developers
* access reports

---

## Manager

Can:

* manage projects
* manage tasks
* manage own team workflow

Cannot:

* assign cross-team users

---

## Developer

Can:

* create/update tasks
* access assigned tasks

Cannot:

* delete tasks
* manage projects

---

## QA

Can:

* review tasks
* access assigned review tasks

Cannot:

* create projects/tasks

---

# 🧠 Business Rules

* Admin users cannot belong to teams
* Admin users cannot be assigned to tasks
* Only one Manager and one QA allowed per team
* Users without teams cannot manage tasks
* Cross-team assignments are restricted to Admin
* Team members only see relevant tasks
* Developers can access cross-team tasks only if assigned

---

# 🔄 Workflow Overview

1. Admin creates teams and users
2. Admin assigns roles and teams
3. Managers create projects and tasks
4. Developers work on assigned tasks
5. QA reviews tasks marked as "In Review"
6. Notifications trigger on assignment updates
7. Reports provide overdue task analytics

---

# 🛠️ Tech Stack

## Backend

* Python
* Django
* Django REST Framework

## Database

* PostgreSQL

## Async & Caching

* Redis
* Celery

## Deployment & Containers

* Docker
* Docker Compose

---

# 🏗️ Project Structure

```bash id="f4s2bn"
TASK_MANAGER_API/
│
├── accounts/
├── config/
├── notifications/
├── projects/
├── tasks/
├── teams/
│
├── .env
├── .gitignore
├── docker-compose.yml
├── Dockerfile
├── manage.py
├── README.md
└── requirements.txt
```

---

# ⚙️ Local Installation

```bash id="q9l1gk"
git clone <repo_url>

cd TASK_MANAGER_API

pip install -r requirements.txt
```

---

# 🔐 Environment Variables

Create a `.env` file:

```env id="qklhn0"
DB_NAME=task_manager
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=db
DB_PORT=5432

SECRET_KEY=your_secret_key

DEBUG=True
```

---

# 🐳 Docker Setup

## Run Project

```bash id="p0pmou"
docker compose up --build
```

---

# Run Migrations

```bash id="l3hbg5"
docker compose exec web python manage.py migrate
```

---

# Create Superuser

```bash id="6pq1zd"
docker compose exec web python manage.py createsuperuser
```

---

# Services Included

* Django App
* PostgreSQL
* Redis
* Celery Worker

---

# 📘 API Documentation

Browsable API available at:

```bash id="jlwmft"
http://127.0.0.1:8000/
```

---

# 🔑 Authentication Flow

## Login

```bash id="mml1t4"
POST /users/login/
```

Returns:

* access token
* refresh token

---

# Refresh Token

```bash id="9l7kz0"
POST /users/token/refresh
```

---

# 👤 User Management Endpoints

## Profile

```bash id="c4p0vn"
GET /users/profile/
```

---

# Change Password

```bash id="1lfbxf"
PATCH /users/profile/change-password/
```

---

# Admin User Management

```bash id="sbo9w7"
GET     /users/
POST    /users/
GET     /users/<id>/
PATCH   /users/<id>/
DELETE  /users/<id>/
```

---

# 👥 Team Endpoints

```bash id="lsm4g1"
GET     /teams/
POST    /teams/
PATCH   /teams/<id>/
DELETE  /teams/<id>/
```

---

# 📁 Project Endpoints

```bash id="4n6g3s"
GET     /projects/
POST    /projects/
PATCH   /projects/<id>/
DELETE  /projects/<id>/
```

---

# ✅ Task Endpoints

```bash id="0az2eh"
GET     /tasks/
POST    /tasks/
PATCH   /tasks/<id>/
DELETE  /tasks/<id>/
```

---

# 🔔 Notification Endpoints

```bash id="qcrxjd"
GET     /notifications/
POST    /notifications/
```

---

# 📊 Report Endpoint

```bash id="rx59q4"
GET /tasks/reports/overdue/
```

---

# 🚀 Future Improvements

* Email notifications
* WebSocket realtime updates
* Task comments
* File attachments
* Activity logs
* Soft delete support
* Advanced analytics dashboard

---

# 🎯 Purpose of This Project

This project was built to practice and demonstrate:

* production-style backend architecture
* DRF workflows
* role-based permissions
* async processing
* Redis caching
* Dockerized services
* raw SQL reporting
* scalable API design

---

# 📄 License

This project is for educational purposes.

---

# 👨‍💻 Author

Khushi Koriya

GitHub: [https://github.com/khushiiik]