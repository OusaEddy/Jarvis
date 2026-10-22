"""PaceSetter's settings: my day, loaded from settings.json."""
from datetime import date
import json
from dataclasses import dataclass
from pathlib import Path

from .clock import to_minutes

SETTINGS_FILE = Path(__file__).parent.parent / "settings.json"
MINUTES_IN_A_DAY = 24 * 60
TIME_SETTINGS = ("wake", "sleep", "work_start", "work_end", "lunch_start", "lunch_end", "focus_start", "focus_end", "low_start", "low_end")
DAYS_OF_WEEK = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


@dataclass
class Settings:
    wake: str
    sleep: str
    work_start: str
    work_end: str
    lunch_start: str
    lunch_end: str
    focus_start: str
    focus_end: str
    low_start: str
    low_end: str
    work_days: list[str]
    min_session: int

    def __post_init__(self):

        # Rule 1: every time setting must be a real time.
        for name in TIME_SETTINGS:
            try:
                self.minutes(name)
            except ValueError as error:
                raise ValueError(f"Settings '{name}': {error}") from None

        # Rule 2: work must start before it ends.
        work_start = self.minutes("work_start")
        work_end = self.minutes("work_end")
        if work_end <= work_start:
            raise ValueError(f"Settings 'work': work_start must be before work_end. (got {self.work_start} to {self.work_end}).") 

        # Rule 3: each window must start before it ends, and fit inside work hours.
        for part in ("lunch", "focus", "low"):
            start = self.minutes(f"{part}_start")
            end = self.minutes(f"{part}_end")
            if not (work_start <= start < end <= work_end):
                start_text = getattr(self, f"{part}_start")
                end_text = getattr(self, f"{part}_end")
                raise ValueError(f"Settings '{part}': must start before it ends and fit inside work hours "
                                 f"{self.work_start}-{self.work_end} (got {start_text} to {end_text})."
                                 )
            
        # Rule 4:  there must be at least one work day, and each must be a real day of the week.
        if not self.work_days:
            raise ValueError("Settings 'work_days': give at least one work day, e.g. [\"Monday\"].")
        for day in self.work_days:
            if day not in DAYS_OF_WEEK:
                raise ValueError(f"Settings 'work_days': '{day}' is not a day of the week. Use one of: {', '.join(DAYS_OF_WEEK)}.")

        #  Rule 5: the shortest session must be a whole number of minutes above 0.
        if not isinstance(self.min_session, int) or self.min_session <= 0:
            raise ValueError(f"Settings 'min_session': must be a whole number above 0, e.g. 30 (got {self.min_session}).")
                

            
    def minutes(self, name: str) -> int:
        return to_minutes(getattr(self, name))

    def bedtime(self) -> int:
        wake = self.minutes("wake")
        sleep = self.minutes("sleep")
        if sleep <= wake:
            sleep += MINUTES_IN_A_DAY
        return sleep

    def is_work_day(self, day: date) -> bool:
        """do I work on this day?"""
        return DAYS_OF_WEEK[day.weekday()] in self.work_days
    
def load_settings(path: Path = SETTINGS_FILE) -> Settings:
    data = json.loads(path.read_text(encoding="utf-8"))
    return Settings(**data)