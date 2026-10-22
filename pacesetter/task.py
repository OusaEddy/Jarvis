from dataclasses import dataclass
import json
from pathlib import Path
from datetime import datetime

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
             done=data.get("done", False),
             id=data.get("id"),
         )

def load_tasks(path: Path = TASKS_FILE) -> list[Task]:
    """All my saved tasks. No file yet means no tasks yet."""
    if not path.exists():
        return []
    data = json.loads(path.read_text(encoding="utf-8"))
    return [Task.from_dict(item) for item in data]

def save_tasks(tasks: list[Task], path: Path = TASKS_FILE) -> None:
    """Save all my tasks to tasks.json, replacing what was there."""
    data = [task.to_dict() for task in tasks]
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")

def add_task(task: Task, path: Path = TASKS_FILE) -> Task:
    """Add one task to my saved tasks."""
    tasks = load_tasks(path)
    if any(t.name == task.name and not t.done for t in tasks):
        raise ValueError(f"'{task.name}' is already on my list. Log progress on it instead of adding it again")
    task.id = max((t.id or 0 for t in tasks), default=0) + 1
    tasks.append(task)
    save_tasks(tasks, path)
    return task

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


def log_work(task_id: int, minutes: int, path: Path = TASKS_FILE) -> Task:
    """Record minutes I actually worked on a task."""
    if not isinstance(minutes, int) or minutes <= 0:
        raise ValueError("Minutes worked must be a whole number above 0, e.g. 45.")
    tasks = load_tasks(path)
    task = find_task(tasks, task_id)
    task.minutes_done += minutes
    save_tasks(tasks, path)
    return task

def mark_done(task_id: int, path: Path = TASKS_FILE) -> Task:
    """Record that a task is finished"""
    tasks = load_tasks(path)
    task = find_task(tasks, task_id)
    task.done = True
    save_tasks(tasks, path)
    return task

