"""Run PaceSetter from the terminal: daily brief, and commands to manage my tasks."""
import argparse
import sys
from datetime import date, datetime

from .alerts import deadline_alerts, event_clashes
from .events import load_events
from .planner import plan_day, print_plan
from .settings import load_settings
from .suggestions import suggestions
from .task import FOCUS, IMPORTANCE, Task, add_task, load_tasks, log_work, mark_done, print_tasks
from .page import open_page, render_page


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
    elif args.command == "tasks":
        print_tasks(load_tasks())
    elif args.command == "add":
        deadline = parse_deadline(args.deadline) if args.deadline else None
        task = add_task(Task(args.name, args.minutes, deadline, args.importance, args.focus))
        print(f"Added [{task.id}] {task.name}")
    elif args.command == "log":
        task = log_work(args.task_id, args.minutes)
        print(f"Logged {args.minutes} min on [{task.id}] {task.name}, {task.remaining()} min left")
    elif args.command == "done":
        task = mark_done(args.task_id)
        print(f"Done: [{task.id}] {task.name}")


def main() -> None:
    """Read what I typed in the terminal and run it."""
    parser = argparse.ArgumentParser(prog="pacesetter", description="PaceSetter plans my day.")
    commands = parser.add_subparsers(dest="command")

    page_cmd = commands.add_parser("page", help="my day as a web page in the browser")
    page_cmd.add_argument("day", nargs="?", help="YYYY-MM-DD (default: today)")


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

    done_cmd = commands.add_parser("done", help="mark a task as finished")
    done_cmd.add_argument("task_id", type=int)

    args = parser.parse_args()
    try:
        run(args)
    except ValueError as error:
        print(f"Sorry: {error}")
        sys.exit(1)


if __name__ == "__main__":
    main()
