"""My day as a web page: PaceSetter writes plan.html and opens it in my browser."""
import html
import webbrowser
from pathlib import Path

from .clock import to_hhmm
from .events import Event
from .planner import DayPlan
from .settings import Settings

PAGE_FILE = Path(__file__).parent.parent / "plan.html"
PIXELS_PER_MINUTE = 1.2

STYLE = """
:root { --ink: #13232e; --muted: #5b6b77; --line: #d5dde3; --bg: #f3f5f7; --card: #ffffff;
        --deep: #0f5f6e; --normal: #2f6fb3; --light: #b7791f; --fixed: #8a96a0;
        --free: #eaf4ed; --free-edge: #5f9c6e; --warn: #a8322a; }
* { box-sizing: border-box; }
body { margin: 0; background: var(--bg); color: var(--ink);
       font: 15px/1.5 "Segoe UI", system-ui, sans-serif; }
main { max-width: 760px; margin: 0 auto; padding: 28px 16px; }
h1 { margin: 0; font-size: 1.7rem; }
.sub { color: var(--muted); margin-bottom: 20px; }
.stats { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 20px; }
.stat { background: var(--card); border: 1px solid var(--line); border-radius: 10px; padding: 10px 16px; }
.stat b { display: block; font-size: 1.35rem; }
.day { background: var(--card); border: 1px solid var(--line); border-radius: 12px; overflow: hidden; }
.row { display: flex; border-top: 1px solid var(--line); }
.row:first-child { border-top: 0; }
.time { width: 120px; flex-shrink: 0; padding: 10px 14px; color: var(--muted);
        font-variant-numeric: tabular-nums; }
.block { flex: 1; padding: 10px 14px; border-left: 6px solid var(--fixed); }
.block small { color: var(--muted); }
.task.deep { border-left-color: var(--deep); }
.task.normal { border-left-color: var(--normal); }
.task.light { border-left-color: var(--light); }
.free { background: var(--free); border-left-color: var(--free-edge); }
.tag { font-size: .75rem; padding: 1px 8px; border-radius: 99px; background: var(--bg);
       border: 1px solid var(--line); margin-left: 8px; }
h2 { font-size: 1.05rem; margin: 26px 0 8px; }
ul { margin: 0; padding-left: 20px; }
.warn li { color: var(--warn); }
footer { color: var(--muted); font-size: .8rem; margin-top: 28px; }
"""


def day_rows(settings: Settings, events: list[Event], plan: DayPlan) -> list[tuple[int, int, str, str, str]]:
    """Everything in my work day, in time order, as (start, end, kind, title, detail)."""
    work_start = settings.minutes("work_start")
    work_end = settings.minutes("work_end")
    rows = []
    for event in events:
        if event.happens_on(plan.day):
            start, end = event.busy()
            start, end = max(start, work_start), min(end, work_end)
            if start < end:
                rows.append((start, end, "fixed", event.name, "Fixed event"))
    rows.append((settings.minutes("lunch_start"), settings.minutes("lunch_end"), "fixed", "Lunch", "Break"))
    for start, end, task in plan.planned:
        session = end - start
        detail = f"{task.importance.capitalize()} importance, {task.focus} focus"
        if session < task.remaining():
            detail += f", {session} of {task.remaining()} min left"
        rows.append((start, end, f"task {task.focus}", task.name, detail))
    for start, end in plan.free_left:
        rows.append((start, end, "free", "Free", f"{end - start} min open"))
    return sorted(rows)


def zone_tag(settings: Settings, start: int) -> str:
    """A small label when a block starts in my focus hours or my low-energy time."""
    if settings.minutes("focus_start") <= start < settings.minutes("focus_end"):
        return '<span class="tag">focus hours</span>'
    if settings.minutes("low_start") <= start < settings.minutes("low_end"):
        return '<span class="tag">low energy</span>'
    return ""


def bullet_list(items: list[str], css_class: str = "") -> str:
    """A list of text as HTML bullet points, made safe for the page."""
    points = "".join(f"<li>{html.escape(item.strip())}</li>" for item in items)
    return f'<ul class="{css_class}">{points}</ul>'


def render_page(settings: Settings, events: list[Event], plan: DayPlan,
                warnings: list[str], options: list[str]) -> str:
    """The whole page as HTML text."""
    rows = []
    for start, end, kind, title, detail in day_rows(settings, events, plan):
        height = max(48, round((end - start) * PIXELS_PER_MINUTE))
        rows.append(
            f'<div class="row" style="min-height:{height}px">'
            f'<div class="time">{to_hhmm(start)} - {to_hhmm(end)}</div>'
            f'<div class="block {kind}"><strong>{html.escape(title)}</strong>{zone_tag(settings, start)}'
            f"<br><small>{html.escape(detail)}</small></div></div>"
        )

    planned_minutes = sum(end - start for start, end, _ in plan.planned)
    free_minutes = sum(end - start for start, end in plan.free_left)
    stats = (
        f'<div class="stat"><b>{len(plan.planned)}</b>tasks planned</div>'
        f'<div class="stat"><b>{planned_minutes} min</b>of planned work</div>'
        f'<div class="stat"><b>{free_minutes} min</b>still free</div>'
    )

    extra = ""
    if plan.not_planned:
        extra += "<h2>Not planned today</h2>" + bullet_list(
            [f"{task.name}: needs {minutes} min" for task, minutes in plan.not_planned]
        )
    if warnings:
        extra += "<h2>Warnings</h2>" + bullet_list(warnings, "warn")
    if options:
        extra += "<h2>Suggestions</h2>" + bullet_list(options)

    return (
        "<!doctype html>\n<html lang='en'>\n<head>\n<meta charset='utf-8'>\n"
        "<meta name='viewport' content='width=device-width, initial-scale=1'>\n"
        f"<title>PaceSetter: {plan.day:%a %d %b}</title>\n<style>{STYLE}</style>\n</head>\n<body>\n<main>\n"
        f"<h1>PaceSetter</h1>\n<div class='sub'>Plan for {plan.day:%A %d %B %Y}</div>\n"
        f"<div class='stats'>{stats}</div>\n<div class='day'>{''.join(rows)}</div>\n{extra}\n"
        "<footer>Made by PaceSetter on this computer. Nothing on this page leaves your laptop.</footer>\n"
        "</main>\n</body>\n</html>\n"
    )


def open_page(page_html: str, path: Path = PAGE_FILE) -> Path:
    """Save the page and open it in my web browser."""
    path.write_text(page_html, encoding="utf-8")
    webbrowser.open(path.as_uri())
    return path
