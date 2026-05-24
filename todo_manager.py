"""
Todo data management and storage layer.
"""

import json
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import List, Optional
from enum import Enum


class Priority(str, Enum):
    """Priority levels for tasks."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"


class Status(str, Enum):
    """Task status."""
    PENDING = "pending"
    COMPLETED = "completed"


@dataclass
class TodoItem:
    """Represents a single todo item."""
    id: int
    task: str
    priority: Priority = Priority.MEDIUM
    status: Status = Status.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    due_date: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "task": self.task,
            "priority": self.priority.value,
            "status": self.status.value,
            "created_at": self.created_at,
            "due_date": self.due_date,
            "completed_at": self.completed_at,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "TodoItem":
        """Create from dictionary."""
        return cls(
            id=data["id"],
            task=data["task"],
            priority=Priority(data.get("priority", "medium")),
            status=Status(data.get("status", "pending")),
            created_at=data.get("created_at", datetime.now().isoformat()),
            due_date=data.get("due_date"),
            completed_at=data.get("completed_at"),
        )


class TodoManager:
    """Manages todo items with persistent JSON storage."""

    DEFAULT_STORAGE = Path.home() / ".todo" / "todos.json"

    def __init__(self, storage_path: Optional[Path] = None):
        """
        Initialize todo manager.

        Args:
            storage_path: Path to JSON storage file (default: ~/.todo/todos.json)
        """
        self.storage_path = Path(storage_path) if storage_path else self.DEFAULT_STORAGE
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self.todos: List[TodoItem] = []
        self._load()

    def add(self, task: str, priority: str = "medium", due_date: Optional[str] = None) -> TodoItem:
        """
        Add a new todo item.

        Args:
            task: Task description
            priority: Priority level (low, medium, high)
            due_date: Optional due date in YYYY-MM-DD format

        Returns:
            Created TodoItem
        """
        task_id = (max((t.id for t in self.todos), default=0)) + 1
        item = TodoItem(
            id=task_id,
            task=task,
            priority=Priority(priority),
            due_date=due_date,
        )
        self.todos.append(item)
        self._save()
        return item

    def complete(self, task_id: int) -> TodoItem:
        """Mark todo as completed."""
        item = self._find_by_id(task_id)
        item.status = Status.COMPLETED
        item.completed_at = datetime.now().isoformat()
        self._save()
        return item

    def delete(self, task_id: int) -> bool:
        """Delete todo by ID."""
        original_len = len(self.todos)
        self.todos = [t for t in self.todos if t.id != task_id]
        if len(self.todos) < original_len:
            self._save()
            return True
        return False

    def update(
        self,
        task_id: int,
        task: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> TodoItem:
        """Update todo item."""
        item = self._find_by_id(task_id)
        if task:
            item.task = task
        if priority:
            item.priority = Priority(priority)
        if due_date is not None:
            item.due_date = due_date
        self._save()
        return item

    def get_all(self) -> List[TodoItem]:
        """Get all todos."""
        return self.todos.copy()

    def get_by_status(self, status: str) -> List[TodoItem]:
        """Get todos by status."""
        return [t for t in self.todos if t.status.value == status]

    def get_by_priority(self, priority: str) -> List[TodoItem]:
        """Get todos by priority."""
        return [t for t in self.todos if t.priority.value == priority]

    def search(self, query: str) -> List[TodoItem]:
        """Search todos by task description."""
        query_lower = query.lower()
        return [t for t in self.todos if query_lower in t.task.lower()]

    def clear_completed(self) -> int:
        """Delete all completed todos."""
        original_len = len(self.todos)
        self.todos = [t for t in self.todos if t.status == Status.PENDING]
        deleted = original_len - len(self.todos)
        if deleted > 0:
            self._save()
        return deleted

    def get_stats(self) -> dict:
        """Get statistics."""
        total = len(self.todos)
        completed = len([t for t in self.todos if t.status == Status.COMPLETED])
        pending = total - completed
        high_priority = len([t for t in self.todos if t.priority == Priority.HIGH])

        return {
            "total": total,
            "completed": completed,
            "pending": pending,
            "completed_percentage": (completed / total * 100) if total > 0 else 0,
            "high_priority": high_priority,
        }

    def _find_by_id(self, task_id: int) -> TodoItem:
        """Find todo by ID or raise error."""
        for item in self.todos:
            if item.id == task_id:
                return item
        raise ValueError(f"Todo with ID {task_id} not found")

    def _load(self) -> None:
        """Load todos from JSON file."""
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r") as f:
                    data = json.load(f)
                    self.todos = [TodoItem.from_dict(item) for item in data]
            except json.JSONDecodeError:
                self.todos = []

    def _save(self) -> None:
        """Save todos to JSON file."""
        with open(self.storage_path, "w") as f:
            json.dump([item.to_dict() for item in self.todos], f, indent=2)
