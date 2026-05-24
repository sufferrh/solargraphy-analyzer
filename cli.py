"""
Command-line interface for todo application.
"""

import sys
from datetime import datetime
from typing import Optional
from tabulate import tabulate
import json
import csv

from todo_manager import TodoManager


class TodoCLI:
    """Command-line interface for todo management."""

    PRIORITY_COLORS = {
        "low": "\033[92m",      # Green
        "medium": "\033[93m",   # Yellow
        "high": "\033[91m",     # Red
    }
    RESET_COLOR = "\033[0m"
    CHECKMARK = "✓"
    CIRCLE = "○"

    def __init__(self, manager: TodoManager):
        """Initialize CLI."""
        self.manager = manager

    def add_todo(
        self,
        task: str,
        priority: str = "medium",
        due_date: Optional[str] = None,
    ) -> None:
        """Add a new todo."""
        try:
            item = self.manager.add(task, priority, due_date)
            print(f"✅ Added todo #{item.id}: {task}")
            if due_date:
                print(f"   📅 Due: {due_date}")
            print(f"   Priority: {self._colorize_priority(priority)}")
        except ValueError as e:
            print(f"❌ Error: {str(e)}", file=sys.stderr)

    def list_todos(
        self,
        filter_by: str = "all",
        sort_by: str = "date",
    ) -> None:
        """List todos with optional filtering and sorting."""
        if filter_by == "pending":
            todos = self.manager.get_by_status("pending")
        elif filter_by == "completed":
            todos = self.manager.get_by_status("completed")
        else:
            todos = self.manager.get_all()

        if not todos:
            print("📭 No todos found")
            return

        # Sort todos
        if sort_by == "priority":
            priority_order = {"high": 0, "medium": 1, "low": 2}
            todos.sort(key=lambda t: priority_order[t.priority.value])
        elif sort_by == "status":
            todos.sort(key=lambda t: t.status.value)
        else:  # date
            todos.sort(key=lambda t: t.created_at, reverse=True)

        # Prepare table data
        table_data = []
        for todo in todos:
            status_icon = self.CHECKMARK if todo.status.value == "completed" else self.CIRCLE
            priority_str = self._colorize_priority(todo.priority.value)
            due = todo.due_date if todo.due_date else "-"
            table_data.append([
                todo.id,
                status_icon,
                todo.task[:40],  # Truncate long tasks
                priority_str,
                due,
            ])

        headers = ["ID", "", "Task", "Priority", "Due Date"]
        print("\n" + tabulate(table_data, headers=headers, tablefmt="grid"))
        print(f"\n📊 Total: {len(todos)} todos\n")

    def complete_todo(self, task_id: int) -> None:
        """Mark todo as completed."""
        try:
            item = self.manager.complete(task_id)
            print(f"✅ Completed: {item.task}")
        except ValueError:
            print(f"❌ Todo #{task_id} not found", file=sys.stderr)

    def delete_todo(self, task_id: int) -> None:
        """Delete a todo."""
        try:
            item = self.manager._find_by_id(task_id)
            task_name = item.task
            self.manager.delete(task_id)
            print(f"🗑️  Deleted: {task_name}")
        except ValueError:
            print(f"❌ Todo #{task_id} not found", file=sys.stderr)

    def update_todo(
        self,
        task_id: int,
        task: Optional[str] = None,
        priority: Optional[str] = None,
        due_date: Optional[str] = None,
    ) -> None:
        """Update a todo."""
        try:
            item = self.manager.update(task_id, task, priority, due_date)
            print(f"✏️  Updated todo #{task_id}")
            if task:
                print(f"   Task: {task}")
            if priority:
                print(f"   Priority: {self._colorize_priority(priority)}")
            if due_date:
                print(f"   Due: {due_date}")
        except ValueError:
            print(f"❌ Todo #{task_id} not found", file=sys.stderr)

    def clear_completed(self) -> None:
        """Clear all completed todos."""
        deleted = self.manager.clear_completed()
        print(f"🗑️  Cleared {deleted} completed todo(s)")

    def show_stats(self) -> None:
        """Display statistics."""
        stats = self.manager.get_stats()
        print("\n📊 TODO STATISTICS")
        print("=" * 40)
        print(f"Total todos:        {stats['total']}")
        print(f"Completed:          {stats['completed']}")
        print(f"Pending:            {stats['pending']}")
        print(f"Completion rate:    {stats['completed_percentage']:.1f}%")
        print(f"High priority:      {stats['high_priority']}")
        print("=" * 40 + "\n")

    def search_todos(self, query: str) -> None:
        """Search todos."""
        results = self.manager.search(query)
        if not results:
            print(f"🔍 No todos found for '{query}'")
            return

        print(f"\n🔍 Found {len(results)} result(s) for '{query}':\n")
        table_data = []
        for todo in results:
            status_icon = self.CHECKMARK if todo.status.value == "completed" else self.CIRCLE
            priority_str = self._colorize_priority(todo.priority.value)
            table_data.append([
                todo.id,
                status_icon,
                todo.task,
                priority_str,
            ])

        headers = ["ID", "", "Task", "Priority"]
        print(tabulate(table_data, headers=headers, tablefmt="grid") + "\n")

    def export_todos(self, format_type: str = "json") -> None:
        """Export todos to file."""
        todos = self.manager.get_all()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format_type == "json":
            filename = f"todos_{timestamp}.json"
            with open(filename, "w") as f:
                json.dump(
                    [todo.to_dict() for todo in todos],
                    f,
                    indent=2,
                )
            print(f"✅ Exported to {filename}")

        elif format_type == "csv":
            filename = f"todos_{timestamp}.csv"
            with open(filename, "w", newline="") as f:
                writer = csv.DictWriter(
                    f,
                    fieldnames=["id", "task", "priority", "status", "due_date"],
                )
                writer.writeheader()
                for todo in todos:
                    writer.writerow({
                        "id": todo.id,
                        "task": todo.task,
                        "priority": todo.priority.value,
                        "status": todo.status.value,
                        "due_date": todo.due_date or "",
                    })
            print(f"✅ Exported to {filename}")

    @staticmethod
    def _colorize_priority(priority: str) -> str:
        """Add color to priority text."""
        color = TodoCLI.PRIORITY_COLORS.get(priority, "")
        return f"{color}{priority}{TodoCLI.RESET_COLOR}"
