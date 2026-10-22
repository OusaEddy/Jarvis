"""Suggestions: options for tasks that didn't fit. PaceSetter suggests; I decide."""
from datetime import date, timedelta

from .clock import to_hhmm
from .events import Event
from .planner import DayPlan, find_slot, free_time, preferred_window
from .settings import Settings
from .task import Task

LOOK_AHEAD_DAYS = 14


def split_option(free: list[tuple[int, int]], minutes: int, min_piece: int) -> list[tuple[int, int]] | None:
    """Pieces of free time, each at least min_piece long, that add up to the minutes needed. None if impossible."""
    pieces = []
    left = minutes
    for start, end in free:
        length = min(end - start, left)
        if length >= min_piece or length == left:
            pieces.append((start, length))
            left -= length
            if left == 0:
                return pieces
    return None


def next_day_option(settings: Settings, events: list[Event], task: Task, minutes: int, day: date) -> tuple[date, int] | None:
    """The first later day, within two weeks, with a free stretch long enough. None if there isn't one."""
    for offset in range(1, LOOK_AHEAD_DAYS + 1):
        later = day + timedelta(days=offset)
        start = find_slot(free_time(settings, events, later), minutes, preferred_window(settings, task))
        if start is not None:
            return later, start
    return None


def suggestions(settings: Settings, events: list[Event], plan: DayPlan) -> list[str]:
    """Options for each task that didn't fit today. Nothing changes until I choose."""
    lines = []
    for task, minutes in plan.not_planned:
        lines.append(f"'{task.name}' needs {minutes} min on {plan.day:%a %d %b} but doesn't fit. Options:")
        pieces = split_option(plan.free_left, minutes, settings.min_session)
        if pieces:
            parts = " + ".join(f"{length} min at {to_hhmm(start)}" for start, length in pieces)
            lines.append(f"  - Split it today: {parts}")
        later = next_day_option(settings, events, task, minutes, plan.day)
        if later:
            later_day, start = later
            too_late = task.deadline is not None and later_day > task.deadline.date()
            note = " (after its deadline!)" if too_late else ""
            lines.append(f"  - Do it on {later_day:%a %d %b} at {to_hhmm(start)}{note}")
        if not pieces and not later:
            lines.append("  - Nothing fits in the next two weeks. Consider a later deadline, or breaking it into smaller tasks.")
    return lines
