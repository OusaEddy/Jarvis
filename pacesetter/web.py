"""PaceSetter in my browser: a small web server that only this laptop can reach."""
import html
import secrets
from datetime import date, datetime, timedelta

from flask import Flask, abort, flash, get_flashed_messages, redirect, request

from .events import load_events
from .page import render_week
from .planner import plan_week
from .settings import load_settings
from .task import FOCUS, IMPORTANCE, Task, add_task, load_tasks, log_work, mark_done

app = Flask(__name__)
app.secret_key = secrets.token_hex(16)
app.config["TRUSTED_HOSTS"] = ["127.0.0.1", "localhost"]

CONFIRM_DONE = "return confirm('Mark this task as done?')"


@app.before_request
def own_page_only() -> None:
    """Refuse any change that wasn't sent from my own PaceSetter page."""
    if request.method == "POST" and request.headers.get("Origin") != request.host_url.rstrip("/"):
        abort(403)


def week_links(first_day: date) -> str:
    """Links to the week before and the week after, so I can move through my weeks."""
    before = first_day - timedelta(days=7)
    after = first_day + timedelta(days=7)
    return (
        f'<nav class="links"><a href="/week/{before}">&larr; Week before</a>'
        f'<a href="/">This week</a>'
        f'<a href="/week/{after}">Week after &rarr;</a></nav>'
    )


def messages() -> str:
    """What just happened (added, logged, refused), shown once at the top of the page."""
    return "".join(
        f'<div class="msg {kind}">{html.escape(text)}</div>'
        for kind, text in get_flashed_messages(with_categories=True)
    )


def options(values: list[str], chosen: str) -> str:
    """The choices for a drop-down list, with one already picked."""
    return "".join(f'<option{" selected" if value == chosen else ""}>{value}</option>' for value in values)


def task_panel(tasks: list[Task]) -> str:
    """My open tasks with a Done button each, and the forms to log work and add a task."""
    active = [task for task in tasks if not task.done]
    rows = "".join(
        f"<tr><td>[{task.id}] {html.escape(task.name)}</td><td>{task.minutes_done}/{task.minutes} min</td>"
        f'<td><form method="post" action="/done/{task.id}" onsubmit="{CONFIRM_DONE}">'
        f"<button>Done</button></form></td></tr>"
        for task in active
    ) or '<tr><td colspan="3">No open tasks.</td></tr>'
    choices = "".join(f'<option value="{task.id}">[{task.id}] {html.escape(task.name)}</option>' for task in active)
    today = date.today().isoformat()
    return f"""
<section class="panel">
  <div class="card"><h2>Open tasks</h2><table>{rows}</table></div>
  <form class="card" method="post" action="/log">
    <h2>Log work</h2>
    <label>Task <select name="task_id" required>{choices}</select></label>
    <label>Minutes worked <input name="minutes" type="number" min="1" required></label>
    <label>Day <input name="day" type="date" value="{today}" max="{today}"></label>
    <button>Log work</button>
  </form>
  <form class="card" method="post" action="/add">
    <h2>Add a task</h2>
    <label>Name <input name="name" maxlength="100" required></label>
    <label>Minutes it takes <input name="minutes" type="number" min="1" required></label>
    <label>Deadline (optional) <input name="deadline" type="datetime-local"></label>
    <label>Importance <select name="importance">{options(IMPORTANCE, "medium")}</select></label>
    <label>Focus <select name="focus">{options(FOCUS, "normal")}</select></label>
    <button>Add task</button>
  </form>
</section>
"""


def show_week(first_day: date) -> str:
    """The week page, read fresh from my files and database every time it loads."""
    settings = load_settings()
    events = load_events()
    tasks = load_tasks()
    plans = plan_week(settings, events, tasks, first_day)
    return render_week(settings, events, plans, messages() + week_links(first_day), task_panel(tasks))


def whole_number(field: str, label: str) -> int:
    """A whole number typed into the form, with a clear message if it isn't one."""
    text = request.form.get(field, "").strip()
    if not text.isdigit():
        raise ValueError(f"{label} must be a whole number above 0, e.g. 45.")
    return int(text)


@app.route("/")
def this_week() -> str:
    """My week, starting today."""
    return show_week(date.today())


@app.route("/week/<day_text>")
def week_from(day_text: str) -> str:
    """The week starting on any day, e.g. /week/2026-10-26."""
    try:
        first_day = date.fromisoformat(day_text)
    except ValueError:
        abort(404)
    return show_week(first_day)


@app.post("/add")
def add():
    """Add a task from the form, through the same rules as the terminal."""
    try:
        deadline_text = request.form.get("deadline", "")
        deadline = datetime.fromisoformat(deadline_text) if deadline_text else None
        task = add_task(Task(
            request.form.get("name", ""),
            whole_number("minutes", "Minutes it takes"),
            deadline,
            request.form.get("importance", ""),
            request.form.get("focus", ""),
        ))
        flash(f"Added [{task.id}] {task.name}", "ok")
    except ValueError as error:
        flash(str(error), "error")
    return redirect("/")


@app.post("/log")
def log():
    """Record work from the form, through the same rules as the terminal."""
    try:
        day_text = request.form.get("day", "")
        day = date.fromisoformat(day_text) if day_text else None
        minutes = whole_number("minutes", "Minutes worked")
        task = log_work(whole_number("task_id", "Task"), minutes, day)
        flash(f"Logged {minutes} min on [{task.id}] {task.name}, {task.remaining()} min left", "ok")
    except ValueError as error:
        flash(str(error), "error")
    return redirect("/")


@app.post("/done/<int:task_id>")
def done(task_id: int):
    """Mark a task finished when I press its Done button."""
    try:
        task = mark_done(task_id)
        flash(f"Done: [{task.id}] {task.name}", "ok")
    except ValueError as error:
        flash(str(error), "error")
    return redirect("/")


def serve(port: int = 5000) -> None:
    """Start the server on this laptop only. Ctrl+C in the terminal stops it."""
    app.run(host="127.0.0.1", port=port)
