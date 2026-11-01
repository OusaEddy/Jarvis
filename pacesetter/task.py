from dataclasses import dataclass
import json
from pathlib import Path
from datetime import date, datetime
from .db import DB_FILE, open_db

TASKS_FILE = Path(__file__).parent.parent / "tasks.json"

IMPORTANCE = ["low", "medium", "high"]
FOCUS = ["normal", "deep", "light"]

@dataclass
class Task:
    name: str
    minutes: int
    deadline: datetime | None = None
    importance: str = "medium"
    focus: str = "normal"
    minutes_done: int = 0
    done: bool = False
    id: int | None = None

    def __post_init__(self):
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("A task needs a name, e.g. 'Finish client proposal'.")
        self.name = self.name.strip()
        if not isinstance(self.minutes, int) or self.minutes <= 0:
            raise ValueError(f"'{self.name}': minutes must be a whole number above 0, e.g. 90.")
        if self.deadline is not None and not isinstance(self.deadline, datetime):
            raise ValueError(f"'{self.name}': the deadline must be a date and time, or left out.")
        if self.importance not in IMPORTANCE:
            raise ValueError(f"'{self.name}': importance must be one of: {', '.join(IMPORTANCE)}.")
        if self.focus not in FOCUS:
            raise ValueError(f"'{self.name}': focus must be one of: {', '.join(FOCUS)}.")
        if not isinstance(self.minutes_done, int) or self.minutes_done < 0:
            raise ValueError(f"'{self.name}': minutes_done must be a whole number, 0 or more.")

    def remaining(self) -> int:
        """ Minutes still to do. A finished task has none left."""
        if self.done:
            return 0
        return max(0, self.minutes - self.minutes_done)

    def to_dict(self) -> dict:
        """The task as plain data, ready to save as JSON"""
        return {
            "id": self.id,
            "name": self.name,
            "minutes": self.minutes,
            "minutes_done": self.minutes_done,
            "done": self.done,
            "deadline": self.deadline.isoformat(timespec="minutes") if self.deadline else None,
            "importance": self.importance,
            "focus": self.focus,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Task":
         """Build a task from saved data, turning the deadline text back into a date and time."""
         deadline = data.get("deadline")
         return cls(
             name=data["name"],
             minutes=data["minutes"],
             deadline=datetime.fromisoformat(deadline) if deadline else None,
             importance=data.get("importance", "medium"),
             focus=data.get("focus", "normal"),
             minutes_done=data.get("minutes_done", 0),
             done=bool(data.get("done", False)),
             id=data.get("id"),
         )

INSERT_TASK = (
    "INSERT INTO tasks(id, name, minutes, deadline, importance, focus, done)"
    "VALUES(:id, :name, :minutes, :deadline, :importance, :focus, :done)"
)
INSERT_LOG = "INSERT INTO work_log (task_id, day, minutes, logged_at) VALUES(?, ?, ?, ?)"
SELECT_TASKS = """
SELECT id, name, minutes, deadline, importance, focus, done,
       (SELECT COALESCE(SUM(work_log.minutes), 0) FROM work_log
       WHERE work_log.task_id = tasks .id) AS minutes_done
FROM tasks
ORDER BY id
"""

def load_tasks(path: Path = DB_FILE) -> list[Task]:
    """All my saved tasks, with minutes done added up from my work log"""
    with open_db(path) as db:
        rows = db.execute(SELECT_TASKS).fetchall()
    return [Task.from_dict(dict(row)) for row in rows]

def add_task(task: Task, path: Path = DB_FILE) -> Task:
    """Add one task to my saved tasks."""
    with open_db(path) as db:
        clash = db.execute("SELECT id FROM tasks WHERE name = ? AND done = 0", (task.name,)).fetchone()
        if clash is not None:
           raise ValueError(f"'{task.name}' is already on my list. Log progress on it instead of adding it again")
        task.id = db.execute(INSERT_TASK, task.to_dict()).lastrowid
    return task

def import_tasks_json(json_path: Path = TASKS_FILE, path: Path = DB_FILE) -> int:
    """Copy my tasks from old tasks.json into the database, once. Returns how many."""
    if not json_path.exists():
        raise ValueError(f"There is no {json_path.name} to import.")
    tasks = [Task.from_dict(item) for item in json.loads(json_path.read_text(encoding="utf-8"))]
    with open_db(path) as db:
        if db.execute("SELECT COUNT(*) FROM tasks").fetchone()[0] > 0:
            raise ValueError(f"The database already has tasks, so nothing was imported.")
        for task in tasks:
            db.execute(INSERT_TASK, task.to_dict())
            if task.minutes_done > 0:
                #The old file kept only a total, not dates, so it goes in as one session today.
                db.execute(INSERT_LOG, (task.id, date.today().isoformat(), task.minutes_done, now_text()))
    return len(tasks)


def print_tasks(tasks: list[Task]) -> None:
    """Show my tasks with their IDs and progress."""
    for task in tasks:
        status = "done" if task.done else f"{task.remaining()} min left"
        print(f"[{task.id}] {task.name}: {task.minutes_done}/{task.minutes} min, {status}")

def find_task(tasks: list[Task], task_id: int) -> Task:
    """The task with this ID, or a clear error if there is none."""
    for task in tasks:
        if task.id == task_id:
            return task
    raise ValueError(f"There is no task with ID {task_id}. See the IDs with: python -m pacesetter tasks")

def now_text() -> str:
    """The current date and time as text, e.g. 2026-10-30T17:05:09."""
    return datetime.now().isoformat(timespec="seconds")


def log_work(task_id: int, minutes: int, day: date | None = None, path: Path = DB_FILE) -> Task:
    """Record minutes I actually worked on a task, and on which day."""
    if not isinstance(minutes, int) or minutes <= 0:
        raise ValueError("Minutes worked must be a whole number above 0, e.g. 45.")
    day = day or date.today()
    if day > date.today():
        raise ValueError(f"{day} hasn't happened yet. Log work after you have done it.")
    task = find_task(load_tasks(path), task_id)
    with open_db(path) as db:
        db.execute(INSERT_LOG, (task.id, day.isoformat(), minutes, now_text()))
    task.minutes_done += minutes
    return task


def mark_done(task_id: int, path: Path = DB_FILE) -> Task:
    """Record that a task is finished."""
    task = find_task(load_tasks(path), task_id)
    with open_db(path) as db:
        db.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task.id,))
    task.done = True
    return task


def load_history(path: Path = DB_FILE) -> list[tuple[str, int, int, str]]:
    """Every work session I logged, oldest first, as (day, minutes, task id, task name)."""
    with open_db(path) as db:
        rows = db.execute(
            "SELECT work_log.day, work_log.minutes, tasks.id, tasks.name "
            "FROM work_log JOIN tasks ON tasks.id = work_log.task_id "
            "ORDER BY work_log.day, work_log.id"
        ).fetchall()
    return [tuple(row) for row in rows]


def print_history(history: list[tuple[str, int, int, str]]) -> None:
    """Show my logged work, one session per line, with a total."""
    if not history:
        print("Nothing logged yet.")
        return
    for day, minutes, task_id, name in history:
        print(f"{day}  {minutes:>4} min  [{task_id}] {name}")
    print(f"Total: {sum(minutes for _, minutes, _, _ in history)} min")



