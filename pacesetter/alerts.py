"""Alerts: early warnings about clashing events and deadlines at risk."""
from datetime import date, timedelta

from .events import Event
from .planner import free_time
from .settings import Settings
from .task import Task


def event_clashes(events: list[Event], day: date) -> list[str]:
    """Fixed events on this day that overlap each other."""
    todays = [event for event in events if event.happens_on(day)]
    alerts = []
    for i, first in enumerate(todays):
        for second in todays[i + 1:]:
            first_start, first_end = first.busy()
            second_start, second_end = second.busy()
            if first_start < second_end and second_start < first_end:
                alerts.append(
                    f"Clash on {day:%a %d %b}: '{first.name}' ({first.start}-{first.end}) "
                    f"overlaps '{second.name}' ({second.start}-{second.end})."
                )
    return alerts


def free_minutes_until(settings: Settings, events: list[Event], start_day: date, deadline: date) -> int:
    """All my free work minutes from start_day up to and including the deadline day."""
    total = 0
    day = start_day
    while day <= deadline:
        total += sum(end - start for start, end in free_time(settings, events, day))
        day += timedelta(days=1)
    return total


def deadline_alerts(settings: Settings, events: list[Event], tasks: list[Task], day: date) -> list[str]:
    """Tasks that are overdue, or that can't be finished in the free time before their deadline."""
    alerts = []
    for task in tasks:
        remaining = task.remaining()
        if remaining == 0 or task.deadline is None:
            continue
        deadline_day = task.deadline.date()
        if deadline_day < day:
            alerts.append(
                f"Overdue: '{task.name}' was due {task.deadline:%a %d %b %H:%M}, {remaining} min still to do."
            )
            continue
        free = free_minutes_until(settings, events, day, deadline_day)
        if remaining > free:
            alerts.append(
                f"At risk: '{task.name}' needs {remaining} min before {task.deadline:%a %d %b}, "
                f"but you only have {free} free work minutes until then."
            )
    return alerts
