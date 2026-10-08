from datetime import datetime, timezone

from bson import ObjectId
from pymongo import MongoClient
from mcp.server import MCPServer


# --------------------------------------------------
# MongoDB
# --------------------------------------------------

MONGO_URI = "mongodb://localhost:27017"

client = MongoClient(MONGO_URI)

db = client["todo_db"]
todos_collection = db["todos"]


# --------------------------------------------------
# MCP Server
# --------------------------------------------------

mcp = MCPServer("Todo MCP Server")


# --------------------------------------------------
# Helpers
# --------------------------------------------------

def todo_to_dict(todo):
    return {
        "id": str(todo["_id"]),
        "title": todo["title"],
        "completed": todo["completed"],
        "createdAt": todo["createdAt"].isoformat(),
        "updatedAt": todo["updatedAt"].isoformat(),
    }


# --------------------------------------------------
# ADD TODO
# --------------------------------------------------

@mcp.tool()
def add_todo(title: str) -> dict:
    """
    Add a new todo.
    """

    now = datetime.now(timezone.utc)

    todo = {
        "title": title,
        "completed": False,
        "createdAt": now,
        "updatedAt": now,
    }

    result = todos_collection.insert_one(todo)

    todo["_id"] = result.inserted_id

    return todo_to_dict(todo)


# --------------------------------------------------
# LIST TODOS
# --------------------------------------------------

@mcp.tool()
def list_todos(completed: bool | None = None) -> list:
    """
    List todos.

    If completed is provided:
    - true  -> completed todos
    - false -> pending todos

    If omitted:
    - return all todos
    """

    query = {}

    if completed is not None:
        query["completed"] = completed

    todos = todos_collection.find(query).sort("createdAt", -1)

    return [todo_to_dict(todo) for todo in todos]


# --------------------------------------------------
# GET TODO
# --------------------------------------------------

@mcp.tool()
def get_todo(todo_id: str) -> dict:
    """
    Get a single todo by ID.
    """

    try:
        object_id = ObjectId(todo_id)
    except Exception:
        return {
            "error": "Invalid todo ID"
        }

    todo = todos_collection.find_one({
        "_id": object_id
    })

    if not todo:
        return {
            "error": "Todo not found"
        }

    return todo_to_dict(todo)


# --------------------------------------------------
# EDIT TODO
# --------------------------------------------------

@mcp.tool()
def edit_todo(todo_id: str, title: str) -> dict:
    """
    Edit the title of an existing todo.
    """

    try:
        object_id = ObjectId(todo_id)
    except Exception:
        return {
            "error": "Invalid todo ID"
        }

    now = datetime.now(timezone.utc)

    result = todos_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "title": title,
                "updatedAt": now,
            }
        }
    )

    if result.matched_count == 0:
        return {
            "error": "Todo not found"
        }

    todo = todos_collection.find_one({
        "_id": object_id
    })

    return todo_to_dict(todo)


# --------------------------------------------------
# COMPLETE TODO
# --------------------------------------------------

@mcp.tool()
def complete_todo(todo_id: str, completed: bool = True) -> dict:
    """
    Mark a todo as completed or pending.
    """

    try:
        object_id = ObjectId(todo_id)
    except Exception:
        return {
            "error": "Invalid todo ID"
        }

    now = datetime.now(timezone.utc)

    result = todos_collection.update_one(
        {"_id": object_id},
        {
            "$set": {
                "completed": completed,
                "updatedAt": now,
            }
        }
    )

    if result.matched_count == 0:
        return {
            "error": "Todo not found"
        }

    todo = todos_collection.find_one({
        "_id": object_id
    })

    return todo_to_dict(todo)


# --------------------------------------------------
# DELETE TODO
# --------------------------------------------------

@mcp.tool()
def delete_todo(todo_id: str) -> dict:
    """
    Delete a todo.
    """

    try:
        object_id = ObjectId(todo_id)
    except Exception:
        return {
            "error": "Invalid todo ID"
        }

    result = todos_collection.delete_one({
        "_id": object_id
    })

    if result.deleted_count == 0:
        return {
            "error": "Todo not found"
        }

    return {
        "success": True,
        "message": "Todo deleted successfully",
        "id": todo_id,
    }


# --------------------------------------------------
# SUMMARY
# --------------------------------------------------

@mcp.tool()
def summarize_todos() -> dict:
    """
    Return a summary of all todos.
    """

    total = todos_collection.count_documents({})

    completed = todos_collection.count_documents({
        "completed": True
    })

    pending = todos_collection.count_documents({
        "completed": False
    })

    return {
        "total": total,
        "completed": completed,
        "pending": pending,
    }


# --------------------------------------------------
# Start MCP server
# --------------------------------------------------

if __name__ == "__main__":
    mcp.run()