import re
from django.db import connection
from projects.models import Project
from tasks.models import Task
from teams.models import Team
from chatbot.models.chat_message import ChatMessage
from accounts.models import User
from .llm_service import chat_with_tools
from notifications.tasks import create_notification
from django.utils.dateparse import parse_date
from django.utils.dateparse import parse_datetime
from django.utils import timezone
from datetime import datetime


def execute_read_only_sql(sql_query: str, user_id: int) -> dict:
    """Executes a read-only SELECT SQL query on the database.
    Only SELECT statements are allowed. Returns query results as a list of dicts.
    """
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    # 1. Validate that the query is a SELECT statement
    clean_query = sql_query.strip()
    if not re.match(r"^\s*SELECT\b", clean_query, re.IGNORECASE):
        return {"error": "Only SELECT queries are allowed."}

    # Check for forbidden write/DDL keywords
    forbidden_keywords = [
        "INSERT",
        "UPDATE",
        "DELETE",
        "DROP",
        "ALTER",
        "TRUNCATE",
        "CREATE",
        "REPLACE",
    ]
    flat_query = " " + " ".join(clean_query.upper().split()) + " "
    for kw in forbidden_keywords:
        if f" {kw} " in flat_query:
            return {"error": f"Write/DDL keyword '{kw}' is prohibited."}

    # 2. Scope checks based on Role and Team
    user_team = user.team
    if user.role != "admin" and not user_team:
        return {"error": "Permission Denied: Users without teams cannot query data."}

    # Run the query
    try:
        with connection.cursor() as cursor:
            cursor.execute(clean_query)
            columns = [col[0] for col in cursor.description]
            rows = cursor.fetchall()

        results = [dict(zip(columns, row)) for row in rows]

        # 3. Post-process results for Manager/Developer/QA to enforce team boundaries
        if user.role != "admin":
            filtered_results = []
            for row in results:
                # Retrieve and validate any referenced entities in the row
                # Let's check Project:
                proj_id = row.get("project_id") or (
                    row.get("id") if "project" in clean_query.lower() else None
                )
                if proj_id and "project" in clean_query.lower():
                    try:
                        proj = Project.objects.get(id=proj_id)
                        if proj.team != user_team:
                            continue  # Filter out row
                    except Project.DoesNotExist:
                        pass

                # Let's check Task:
                task_id = row.get("task_id") or (
                    row.get("id") if "task" in clean_query.lower() else None
                )
                if task_id and "task" in clean_query.lower():
                    try:
                        task = Task.objects.get(id=task_id)
                        # Check team boundaries OR if it is assigned to this user
                        is_assigned_to_user = (
                            task.assigned_to and task.assigned_to.id == user.id
                        )
                        if task.project.team != user_team and not is_assigned_to_user:
                            continue  # Filter out row
                    except Task.DoesNotExist:
                        pass

                # Let's check User:
                usr_id = row.get("user_id") or (
                    row.get("id") if "user" in clean_query.lower() else None
                )
                if usr_id and "user" in clean_query.lower():
                    try:
                        u = User.objects.get(id=usr_id)
                        if u.team != user_team:
                            continue  # Filter out row
                    except User.DoesNotExist:
                        pass

                filtered_results.append(row)
            results = filtered_results

        # Clean results for JSON serialization (convert datetimes, dates, UUIDs to string)
        import datetime
        import uuid

        cleaned_results = []
        for row in results:
            cleaned_row = {}
            for k, v in row.items():
                if isinstance(v, (datetime.datetime, datetime.date)):
                    cleaned_row[k] = v.isoformat()
                elif isinstance(v, uuid.UUID):
                    cleaned_row[k] = str(v)
                else:
                    cleaned_row[k] = v
            cleaned_results.append(cleaned_row)
        results = cleaned_results

        return {"columns": columns, "rows": results}
    except Exception as e:
        return {"error": f"Database error: {str(e)}"}


def assign_task_tool(task_id: int, username: str, user_id: int) -> dict:
    """Assigns an existing task to a user.
    Only admins, managers, developers, and QAs (within their team) can assign tasks.
    """
    try:
        requesting_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    # Validate permission role
    if not requesting_user.role:
        return {"error": "Permission Denied: You cannot assign tasks."}

    if requesting_user.role != "admin" and not requesting_user.team:
        return {"error": "Permission Denied: Users without teams cannot manage tasks."}

    try:
        task = Task.objects.get(id=task_id)
    except Task.DoesNotExist:
        return {"error": f"Task with id={task_id} not found."}

    try:
        assignee = User.objects.get(username=username)
    except User.DoesNotExist:
        return {"error": f"User with username='{username}' not found."}

    # Enforce constraints
    if assignee.role == "admin":
        return {"error": "Validation Error: Admin users cannot be assigned to tasks."}

    # Scoping for non-admin
    if requesting_user.role != "admin":
        # Check task belongs to team
        if task.project.team != requesting_user.team:
            return {
                "error": "Permission Denied: You can only assign tasks within your team's projects."
            }
        # Check assignee belongs to team
        if assignee.team != requesting_user.team:
            return {
                "error": (
                    "Permission Denied: You can only assign tasks "
                    f"to members of your own team ({requesting_user.team.name})."
                )
            }

    old_assigned_to = task.assigned_to
    task.assigned_to = assignee
    task.last_updated_by = requesting_user
    task.save()

    if old_assigned_to != assignee and assignee:
        from notifications.tasks import create_notification

        create_notification.delay(assignee.id, f"You were assigned task: {task.title}")

    return {
        "success": True,
        "message": f"Task '{task.title}' successfully assigned to {assignee.username}.",
    }


def create_task_tool(
    title: str,
    project_name: str,
    description: str = "",
    priority: bool = False,
    deadline: str = None,
    assigned_to_username: str = None,
    user_id: int = None,
) -> dict:
    """Creates a new task within a project.
    Only admins and managers/developers can create tasks.
    """
    try:
        requesting_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    if requesting_user.role not in ["admin", "manager", "developer"]:
        return {"error": "Permission Denied: QA cannot create tasks."}

    if requesting_user.role != "admin" and not requesting_user.team:
        return {"error": "Permission Denied: Users without teams cannot create tasks."}

    # Fetch project
    try:
        if requesting_user.role != "admin":
            project = Project.objects.get(name=project_name, team=requesting_user.team)
        else:
            project = Project.objects.get(name=project_name)
    except Project.DoesNotExist:
        return {
            "error": (
                f"Project '{project_name}' not found or you do not have permission "
                "to access it."
            )
        }

    # Fetch assignee
    assignee = None
    if assigned_to_username:
        try:
            assignee = User.objects.get(username=assigned_to_username)
            if assignee.role == "admin":
                return {
                    "error": (
                        "Validation Error: Admin users cannot be assigned to tasks."
                    )
                }
            if (
                requesting_user.role != "admin"
                and assignee.team != requesting_user.team
            ):
                return {
                    "error": (
                        "Permission Denied: You can only assign tasks to users "
                        f"on your team ({requesting_user.team.name})."
                    )
                }
        except User.DoesNotExist:
            return {"error": f"User with username='{assigned_to_username}' not found."}

    # Parse deadline
    parsed_deadline = None
    if deadline:
        parsed_deadline = parse_datetime(deadline)
        if not parsed_deadline:
            for fmt in ("%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
                try:
                    parsed_deadline = timezone.make_aware(
                        datetime.strptime(deadline, fmt)
                    )
                    break
                except ValueError:
                    continue

    task = Task.objects.create(
        title=title,
        description=description,
        project=project,
        assigned_to=assignee,
        priority=priority,
        deadline=parsed_deadline,
        created_by=requesting_user,
        last_updated_by=requesting_user,
    )

    if assignee:
        create_notification.delay(assignee.id, f"You were assigned task: {task.title}")

    return {
        "success": True,
        "message": f"Task '{task.title}' created successfully in project '{project.name}'.",
        "task_id": task.id,
    }


def create_project_tool(
    name: str, start_date: str = None, end_date: str = None, user_id: int = None
) -> dict:
    """Creates a new project.
    Only admins and managers can create projects.
    """
    try:
        requesting_user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return {"error": "User not found."}

    # Role check
    if requesting_user.role not in ["admin", "manager"]:
        return {
            "error": "Permission Denied: Only Admins and Managers can create projects."
        }

    # Manager must have a team
    if requesting_user.role == "manager" and not requesting_user.team:
        return {
            "error": "Permission Denied: Managers without teams cannot create projects."
        }

    team = requesting_user.team if requesting_user.role == "manager" else None

    # Parse dates

    p_start_date = parse_date(start_date) if start_date else None
    p_end_date = parse_date(end_date) if end_date else None

    project = Project.objects.create(
        name=name,
        is_active=True,
        team=team,
        created_by=requesting_user,
        last_updated_by=requesting_user,
        start_date=p_start_date,
        end_date=p_end_date,
    )

    return {
        "success": True,
        "message": (
            f"Project '{project.name}' created successfully"
            f"{' for team ' + team.name if team else ''}."
        ),
        "project_id": project.id,
    }


def run_db_agent(prompt: str, user_id: int, session_id: str = None) -> str:
    """Run the DB Agent using SQL execution and write tools, enforcing strict permissions and confirmations."""
    try:
        user = User.objects.get(id=user_id)
        role = user.role or "developer"
        team_name = user.team.name if user.team else "None"
        team_id = user.team.id if user.team else "None"
    except User.DoesNotExist:
        return "Error: User context not found."

    # Fetch previous messages for the session to form conversational history
    history = []
    if session_id:
        from chatbot.models.chat_message import ChatMessage

        messages = ChatMessage.objects.filter(session_id=session_id).order_by("id")
        if messages.count() > 1:
            for msg in list(messages)[:-1]:  # exclude the last message, which is the current prompt
                if "Error executing Groq" in msg.content or "<function=" in msg.content:
                    continue
                m_role = "user" if msg.role == ChatMessage.Role.USER else "model"
                history.append({"role": m_role, "parts": [msg.content]})

    system_instruction = (
        "You are an AI database assistant for a Task Manager application. "
        "You help users search and modify tasks, projects, and teams using specialized tool functions. "
        f"The current user has ID {user_id}, Role '{role}', and belongs to Team '{team_name}' (ID {team_id}).\n\n"
        "DATABASE SCHEMA DETAILS:\n"
        "- `tasks_task`: contains fields id, title, description, state (draft/in_progress/in_review/completed/blocked/cancelled), "
        "priority (bool), deadline (datetime), project_id, assigned_to_id, created_by_id, last_updated_by_id, created_at, updated_at.\n"
        "- `projects_project`: contains fields id, name, is_active (bool), team_id, created_by_id, last_updated_by_id, start_date, end_date.\n"
        "- `teams_team`: contains fields id, name, created_at, updated_at.\n"
        "- `accounts_user`: contains fields id, username, email, role (admin/manager/developer/qa), team_id.\n\n"
        "STRICT SECURITY & UI RULES:\n"
        "0. CRITICAL TOOL CALLING RULE: When you decide to invoke a tool, you MUST ONLY output the native tool call using the tools parameter. Do NOT generate any conversational text, thoughts, reasoning, markdown blocks, or custom XML tags in the same turn. Speak to the user only in conversational turns where you do not call tools.\n"
        "1. NEVER output database IDs (project, team, user, or task IDs) in the chat response. Always display names, titles, or usernames instead.\n"
        "2. READ queries: Use the `execute_read_only_sql` tool to fetch data. Admin can view everything. Managers, Developers, and QA can only view "
        "data within their team, plus tasks from other teams assigned to them. (The backend tool will automatically filter out rows violating this, "
        "so rely on the tool's output).\n"
        "3. WRITE / UPDATE queries: To assign a task, create a task, or create a project, you MUST use the specialized write tools: "
        "`assign_task_tool`, `create_task_tool`, or `create_project_tool` respectively. Never generate raw SQL insert/update statements.\n"
        "4. DOUBLE CONFIRMATION REQUIREMENT: Before calling any write tools, you MUST first describe the proposed action "
        "and request the user's explicit confirmation in the chat. For example:\n"
        "   'I am about to create a task: [title], assigned to: [username], belonging to team: [team_name], related to project: [project_name]. Please confirm these changes.'\n"
        "   Do NOT invoke the tool function until the user responds with 'yes', 'confirm', or equivalent agreement.\n"
        "   When the user confirms (e.g., says 'yes', 'confirm', or 'proceed'), you MUST call the write tool using the exact parameters (such as project_name, title, assigned_to_username, etc.) specified in your previous confirmation message or in the original prompt. DO NOT invent or substitute parameters (do not change 'Project Alpha 1' to other names like 'Website Redesign' or 'Home tasks').\n"
        "5. PROJECT/TASK CREATION WORKFLOW: Only Admins and Managers can create projects. Managers/Developers/Admins can create tasks. QAs cannot create either. "
        "When a user asks to create a task, you MUST first run a SELECT query using the 'execute_read_only_sql' tool (e.g., on `projects_project` and `teams_team` tables) to check if the project exists. If it exists, retrieve its team and use that team's name in your confirmation message. If the project does not exist, ask the user if they'd like to create the project first. "
        "Ask the user ONLY for the mandatory details (e.g. project name) and check if they need to add optional details (like assignee, deadline). If they say 'No', proceed with defaults.\n"
        "   Before proposing to create a new project or team, you MUST first query the database using 'execute_read_only_sql' (e.g. checking `projects_project` or `teams_team` tables) to check if a project or team with that name already exists. If it already exists, DO NOT ask to create it; instead, use/associate the existing project or team and inform the user that it already exists.\n"
        "6. TASK ASSIGNMENT LOOKUP: The `assign_task_tool` takes an integer `task_id`. You MUST never pass a task title string (like 'XYZ_123_ABC') directly to this parameter. When a user asks to assign a task by its name/title, you MUST first query the database using 'execute_read_only_sql' to find the task's integer ID, and then pass that integer ID as `task_id` when calling `assign_task_tool`.\n"
    )

    tools = [
        execute_read_only_sql,
        assign_task_tool,
        create_task_tool,
        create_project_tool,
    ]
    return chat_with_tools(
        prompt, tools, system_instruction=system_instruction, history=history
    )
