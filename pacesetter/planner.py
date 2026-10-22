import math
from datetime import date, datetime, timedelta
from dataclasses import dataclass
from .clock import to_hhmm
from .task import Task
from .events import Event
from .settings import DAYS_OF_WEEK, Settings

IMPORTANCE_ORDER = {"high": 0, "medium": 1, "low": 2}
ROUND_TO = 5

@dataclass
class DayPlan:
    """One day's plan: what was placed, what didn't fit, and the free time left over."""
    day: date
    planned: list[tuple[int, int, Task]]
    not_planned: list[tuple[Task, int]]
    free_left: list[tuple[int, int]]

def remove_busy(free: list[tuple[int, int]], busy: tuple[int, int]) -> list[tuple[int, int]]:
    """Cut a busy stretch out of a list of free stretches."""
    busy_start, busy_end = busy
    result = []
    for start, end in free:
        if end <= busy_start or start >= busy_end:
            result.append((start, end))
            continue
        if start < busy_start:
            result.append((start, busy_start))
        if end > busy_end:
            result.append((busy_end, end))
    return result

def within(free: list[tuple[int, int]], window: tuple[int, int]) -> list[tuple[int, int]]:
    """The parts of the stretches that fall inside a window, e.g. my focus hours."""
    window_start, window_end = window
    result = []
    for start, end in free:
        overlap_start = max(start, window_start)
        overlap_end = min(end, window_end)
        if overlap_start < overlap_end:
            result.append((overlap_start, overlap_end))
    return result

def find_slot(free: list[tuple[int, int]], minutes: int, preferred: tuple[int, int] | None = None) -> int | None:
    """Earliest start time for a slot of the given length, optionally within a preferred window."""
    choices = []
    if preferred is not None:
        choices.append(within(free, preferred))
    choices.append(free)
    for stretches in choices:
        for start, end in stretches:
            if end - start >= minutes:
                return start
    return None

def preferred_window(settings: Settings, task: Task) -> tuple[int, int] | None:
    """The preferred window for a task, e.g. my focus hours for a deep task."""
    if task.focus == "deep":
        return (settings.minutes("focus_start"), settings.minutes("focus_end"))
    if task.focus == "light":
        return (settings.minutes("low_start"), settings.minutes("low_end"))
    return None

def free_time(settings: Settings, events: list[Event], day: date) -> list[tuple[int, int]]:
    """The free stretches of my work day: work hours minus lunch."""
    if not settings.is_work_day(day):
        return []
    work = (settings.minutes("work_start"), settings.minutes("work_end"))
    lunch = (settings.minutes("lunch_start"), settings.minutes("lunch_end"))
    free = remove_busy([work], lunch)
    for event in events:
        if event.happens_on(day):
            free = remove_busy(free, event.busy())
    return free

def priority(task: Task) -> tuple[int, datetime]:
    """Sort tasks by importance, then deadline (earliest first)."""
    return (IMPORTANCE_ORDER[task.importance], task.deadline or datetime.max)

def work_days_left(settings: Settings, today: date, deadline: date) -> int:
    """How many of my work days there are from today up to and including the deadline day."""
    count = 0
    day = today
    while day <= deadline:
        if settings.is_work_day(day):
            count += 1
        day += timedelta(days=1)
    return count

def session_minutes(settings: Settings, task: Task, day: date) -> int:
    """How long to work on a task on this day: its fair daily share, never less than my minimum session."""
    remaining = task.remaining()
    if task.deadline is None:
        return remaining
    days = work_days_left(settings, day, task.deadline.date())
    if days <= 1:
        return remaining
    share = math.ceil(remaining / days / ROUND_TO) * ROUND_TO
    return min(remaining, max(settings.min_session, share))

def plan_day(settings: Settings, events: list[Event], tasks: list[Task], day: date) -> DayPlan:
    """Plan a day: return a list of (planned, not_planned) tuples."""
    free = free_time(settings, events, day)
    planned = []
    not_planned = []
    for task in sorted(tasks, key=priority):
        minutes = session_minutes(settings, task, day)
        if minutes == 0:
            continue
        start = find_slot(free, minutes, preferred_window(settings, task))
        if start is None:
            not_planned.append((task, minutes))
            continue
        end = start + minutes
        planned.append((start, end, task))
        free = remove_busy(free, (start, end))
    planned.sort(key=lambda item: item[0])
    return DayPlan(day, planned, not_planned, free)


def print_plan(plan: DayPlan) -> None:
    """Show a day plan as a timetable."""
    print(f"Plan for {plan.day:%A %d %B}")
    for start, end, task in plan.planned:
        session = end - start
        progress = "" if session == task.remaining() else f", {session} of {task.remaining()} min left"
        print(f"  {to_hhmm(start)}-{to_hhmm(end)}  {task.name}  ({task.importance}, {task.focus}{progress})")
    for task, minutes in plan.not_planned:
        print(f"  Not planned: {task.name} (needs {minutes} min today)")
    free_total = sum(end - start for start, end in plan.free_left)
    print(f"  Free work time left: {free_total} min")

    

