"""
Web interface for todo application using Flask.
"""

from flask import Flask, render_template, request, jsonify
from pathlib import Path

from todo_manager import TodoManager

app = Flask(__name__, template_folder="templates")
manager = TodoManager()


@app.route("/")
def index():
    """Render main page."""
    return render_template("index.html")


@app.route("/api/todos", methods=["GET"])
def get_todos():
    """Get all todos as JSON."""
    filter_by = request.args.get("filter", "all")
    sort_by = request.args.get("sort", "date")

    if filter_by == "pending":
        todos = manager.get_by_status("pending")
    elif filter_by == "completed":
        todos = manager.get_by_status("completed")
    else:
        todos = manager.get_all()

    # Sort
    if sort_by == "priority":
        priority_order = {"high": 0, "medium": 1, "low": 2}
        todos.sort(key=lambda t: priority_order[t.priority.value])
    elif sort_by == "status":
        todos.sort(key=lambda t: t.status.value)
    else:
        todos.sort(key=lambda t: t.created_at, reverse=True)

    return jsonify([todo.to_dict() for todo in todos])


@app.route("/api/todos", methods=["POST"])
def create_todo():
    """Create a new todo."""
    data = request.json
    task = data.get("task")
    priority = data.get("priority", "medium")
    due_date = data.get("due_date")

    if not task:
        return jsonify({"error": "Task is required"}), 400

    todo = manager.add(task, priority, due_date)
    return jsonify(todo.to_dict()), 201


@app.route("/api/todos/<int:task_id>", methods=["PUT"])
def update_todo(task_id):
    """Update a todo."""
    try:
        data = request.json
        todo = manager.update(
            task_id,
            task=data.get("task"),
            priority=data.get("priority"),
            due_date=data.get("due_date"),
        )
        return jsonify(todo.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/todos/<int:task_id>/complete", methods=["POST"])
def complete_todo(task_id):
    """Mark todo as completed."""
    try:
        todo = manager.complete(task_id)
        return jsonify(todo.to_dict())
    except ValueError as e:
        return jsonify({"error": str(e)}), 404


@app.route("/api/todos/<int:task_id>", methods=["DELETE"])
def delete_todo(task_id):
    """Delete a todo."""
    if manager.delete(task_id):
        return "", 204
    return jsonify({"error": "Todo not found"}), 404


@app.route("/api/todos/clear-completed", methods=["POST"])
def clear_completed():
    """Clear all completed todos."""
    deleted = manager.clear_completed()
    return jsonify({"deleted": deleted})


@app.route("/api/stats", methods=["GET"])
def get_stats():
    """Get statistics."""
    return jsonify(manager.get_stats())


@app.route("/api/search", methods=["GET"])
def search():
    """Search todos."""
    query = request.args.get("q", "")
    if not query:
        return jsonify([])
    todos = manager.search(query)
    return jsonify([todo.to_dict() for todo in todos])


if __name__ == "__main__":
    app.run(debug=True, port=5000)
