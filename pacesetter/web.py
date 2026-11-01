"""Pacesetter in my browser: A small web server only my laptop can reach."""
from datetime import date, timedelta

from flask import Flask, abort

from .events import load_events
from .page import render_week
from .planner import plan_week
from .settings import load_settings
from .task import load_tasks

app = Flask(__name__)

def week_links(first_day: date) -> str:
    """Links to the week before and the week after, so I can move through my weeks."""
    before = first_day - timedelta(days=7)
    after = first_day + timedelta(days=7)
    return (
        f'<nav class="links"><a href="/week/{before}">&larr; Week before</a>'
        f'<a href="/">This week</a>'
        f'<a href="/week/{after}">Week after rarr;</a></nav>'
    )

def show_week(first_day: date) -> str:
    """The week as a web page, with links to the weeks before and after."""
    settings = load_settings()
    events = load_events()
    plans = plan_week(settings, events, load_tasks(), first_day)
    return render_week(settings, events, plans, week_links(first_day))

@app.route("/")
def this_week() -> str:
    """My week, starting today."""
    return show_week(date.today())

@app.route("/week/<day_text>")
def week_from(day_text: str) -> str:
    """The week starting on any day, eg 2026-10-26."""
    try:
        first_day = date.fromisoformat(day_text)
    except ValueError:
        abort(404)
    return show_week(first_day)

def serve(port: int = 5000) -> None:
    """Start the server on this laptop only. Ctrl+C in the terminal stops it."""
    app.run(host="127.0.0.1", port=port)
