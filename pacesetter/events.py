"""Fixed events: things with a set time, like meetings, that PaceSetter plans around."""
import json
from dataclasses import dataclass
from datetime import date
from os import path
from pathlib import Path

from  .clock import to_minutes
from .settings import DAYS_OF_WEEK

EVENTS_FILE = Path(__file__).parent.parent / "events.json"


@dataclass
class Event:
    name: str
    start: str                            #"10:00"
    end: str                              #"11:30"
    on_date: str | None = None            # "2024-06-01"
    days: list[str] | None = None         # repeating event: ["Monday", "Tuesday"]

    def __post_init__(self):
        #Rule 1: it needs a name, without spaces at the ends
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("An event needs a name, e.g. 'Team meeting'.")
        self.name = self.name.strip()

        #Rule 2: start and end are real times, and it starts before it ends
        try:
            start = to_minutes(self.start)
            end = to_minutes(self.end)
        except ValueError as error:
            raise ValueError(f"Event '{self.name}': {error}") from None
        if end <= start:
            raise ValueError(
                f"Event '{self.name}': it must start before it ends (got {self.start} to {self.end})."
            )

        #Rule 3: it is either one-off or repeating: exactly one of on_date / days
        if self.on_date is None and self.days is None:
            raise ValueError(f"Event '{self.name}': give either on_date (one-off) or days (repeating).")
        if self.on_date is not None and self.days is not None:
            raise ValueError(f"Event '{self.name}': give on_date or days, not both.")

        #Rule 4: a one-off date must be a real date
        if self.on_date is not None:
            try:
                date.fromisoformat(self.on_date)
            except ValueError:
                raise ValueError(
                    f"Event '{self.name}': on_date '{self.on_date}' is not a date. Use YYYY-MM-DD, e.g. 2026-10-20."
                ) from None

        #Rule 5: repeating days must be real days of the week, and at least one
        if self.days is not None:
            if not self.days:
                raise ValueError(f"Event '{self.name}': give at least one day, e.g. [\"Monday\"].")
            for day in self.days:
                if day not in DAYS_OF_WEEK:
                    raise ValueError(
                        f"Event '{self.name}': '{day}' is not a day of the week. "
                        f"Use one of: {', '.join(DAYS_OF_WEEK)}."
                    )

    def happens_on(self, day: date) -> bool:
        """Does this event happen on the given day?"""
        if self.on_date is not None:
            return date.fromisoformat(self.on_date) == day
        return DAYS_OF_WEEK[day.weekday()] in self.days

    def busy(self) -> tuple[int, int]:
        """The event as a busy stretch in minutes, ready for remove_busy."""
        return (to_minutes(self.start), to_minutes(self.end))


def load_events(path: Path = EVENTS_FILE) -> list[Event]:
    """All my fixed events, loaded from events.json."""
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Event(**item) for item in data]

