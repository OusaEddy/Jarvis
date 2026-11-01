"""Run PaceSetter from the terminal: daily brief, and commands to manage my tasks."""
import argparse
import sys
from pathlib import Path
from datetime import date, datetime

from .alerts import deadline_alerts, event_clashes
from .events import load_events
from .planner import plan_day, plan_week, print_plan, print_week
from .settings import load_settings
from .suggestions import suggestions
from .db import DB_FILE
from .task import (FOCUS, IMPORTANCE, TASKS_FILE, Task, add_task, import_tasks_json, load_history,
                   load_tasks, log_work, mark_done, print_history, print_tasks)
from .page import WEEK_FILE, open_page, render_page, render_week


def gather(day: date):
    """Everything PaceSetter knows about a day: settings, events, plan, warnings and suggestions."""
    settings = load_settings()
    events = load_events()
    tasks = load_tasks()
    plan = plan_day(settings, events, tasks, day) if settings.is_work_day(day) else None
    options = suggestions(settings, events, plan) if plan is not None else []
    warnings = event_clashes(events, day) + deadline_alerts(settings, events, tasks, day)
    return settings, events, plan, warnings, options


def brief(day: date) -> None:
    """Everything I need to know about one day, in the terminal."""
    settings, events, plan, warnings, options = gather(day)
    if plan is not None:
        print_plan(plan)
    else:
        print(f"{day:%A %d %B} is not a work day, so nothing is planned.")
    if warnings:
        print("\nWarnings")
        for line in warnings:
            print(f"  {line}")
    if options:
        print("\nSuggestions")
        for line in options:
            print(f"  {line}")


def page(day: date) -> None:
    """My day as a web page, opened in my browser."""
    settings, events, plan, warnings, options = gather(day)
    if plan is None:
        print(f"{day:%A %d %B} is not a work day, so there is no plan page.")
        return
    path = open_page(render_page(settings, events, plan, warnings, options))
    print(f"Opened {path.name} in your browser.")


def parse_day(text: str) -> date:
    """Turn '2026-10-21' into a date, with a clear message if it isn't one."""
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise ValueError(f"'{text}' is not a date. Use YYYY-MM-DD, e.g. 2026-10-21.") from None


def parse_deadline(text: str) -> datetime:
    """Turn '2026-10-30 17:00' into a date and time, with a clear message if it isn't one."""
    try:
        return datetime.fromisoformat(text)
    except ValueError:
        raise ValueError(f"'{text}' is not a date and time. Use \"YYYY-MM-DD HH:MM\", e.g. \"2026-10-30 17:00\".") from None



def run(args: argparse.Namespace) -> None:
    """Carry out the command I typed."""
    if args.command in (None, "brief"):
        day_text = getattr(args, "day", None)
        brief(parse_day(day_text) if day_text else date.today())

    elif args.command == "page":
        page(parse_day(args.day) if args.day else date.today())
    elif args.command == "week":
        settings = load_settings()
        events = load_events()
        first_day = parse_day(args.day) if args.day else date.today()
        plans = plan_week(settings, events, load_tasks(), first_day)
        if args.page:
            path = open_page(render_week(settings, events, plans), WEEK_FILE)
            print(f"Opened {path.name} in your browser.")
        else:
            print_week(settings, plans)
    elif args.command == "tasks":
        print_tasks(load_tasks())
    elif args.command == "add":
        deadline = parse_deadline(args.deadline) if args.deadline else None
        task = add_task(Task(args.name, args.minutes, deadline, args.importance, args.focus))
        print(f"Added [{task.id}] {task.name}")
    elif args.command == "history":
        print_history(load_history())
    elif args.command == "import-json":
        count = import_tasks_json(args.file)
        print(f"imported {count} tasks from {args.file.name} into {DB_FILE.name}.")
    elif args.command == "log":
        day = parse_day(args.day) if args.day else None
        task = log_work(args.task_id, args.minutes, day)
        print(f"Logged {args.minutes} min on [{task.id}] {task.name}, {task.remaining()} min left")
    elif args.command == "done":
        task = mark_done(args.task_id)
        print(f"Done: [{task.id}] {task.name}")
    elif args.command == "serve":
        from .web import serve
        serve(args.port)
    


def main() -> None:
    """Read what I typed in the terminal and run it."""
    parser = argparse.ArgumentParser(prog="pacesetter", description="PaceSetter plans my day.")
    commands = parser.add_subparsers(dest="command")

    page_cmd = commands.add_parser("page", help="my day as a web page in the browser")
    page_cmd.add_argument("day", nargs="?", help="YYYY-MM-DD (default: today)")

    week_cmd = commands.add_parser("week", help="the next 7 days, one line per day")
    week_cmd.add_argument("day", nargs="?", help="first day, YYYY-MM-DD (default: today)")
    week_cmd.add_argument("--page", action="store_true", help="show the week as a web page")


    brief_cmd = commands.add_parser("brief", help="plan, warnings and suggestions for a day")
    brief_cmd.add_argument("day", nargs="?", help="YYYY-MM-DD (default: today)")

    commands.add_parser("tasks", help="list my tasks and their progress")

    add_cmd = commands.add_parser("add", help="add a task")
    add_cmd.add_argument("name", help='in quotes if it has spaces, e.g. "Write report"')
    add_cmd.add_argument("minutes", type=int, help="how long it takes")
    add_cmd.add_argument("--deadline", help='e.g. "2026-10-30 17:00"')
    add_cmd.add_argument("--importance", choices=IMPORTANCE, default="medium")
    add_cmd.add_argument("--focus", choices=FOCUS, default="normal")

    log_cmd = commands.add_parser("log", help="record minutes I worked on a task")
    log_cmd.add_argument("task_id", type=int)
    log_cmd.add_argument("minutes", type=int)
    log_cmd.add_argument("--day", help="the day I did it,YYYY-MM-DD (default: today)")

    commands.add_parser("history", help="every work session I logged")

    import_cmd = commands.add_parser("import-json", help="copy tasks from a JSON file into the database, once")
    import_cmd.add_argument("file", nargs="?", type=Path, default=TASKS_FILE, help="default: tasks.json")

    done_cmd = commands.add_parser("done", help="mark a task as finished")
    done_cmd.add_argument("task_id", type=int)

    serve_cmd = commands.add_parser("serve", help="Pacesetter live in my browser, on this laptop only")
    serve_cmd.add_argument("--port", type=int, default=5000, help="default: 5000")

    args = parser.parse_args()
    try:
        run(args)
    except ValueError as error:
        print(f"Sorry: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
