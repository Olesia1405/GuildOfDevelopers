from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

app = FastAPI()

class Task(BaseModel):
    title: str
    description: str
    due_date: Optional[str]
    tags: Optional[List[str]]
    completed: bool = False
    created_at: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "title": "Task Title",
                "description": "Task Description",
                "due_date": "2024-12-31",
                "tags": ["tag1", "tag2"],
                "completed": False,
                "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            }
        }

tasks = []

@app.post("/tasks/")
async def create_task(task: Task):
    task.created_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    tasks.append(task)
    return task

@app.get("/tasks/")
async def read_tasks(
    tag: Optional[str] = None,
    completed: Optional[bool] = None,
    sort_by: Optional[str] = None,
    page: int = 1,
    page_size: int = 10
):
    filtered_tasks = tasks
    if tag:
        filtered_tasks = [task for task in filtered_tasks if tag in task.tags]
    if completed is not None:
        filtered_tasks = [task for task in filtered_tasks if task.completed == completed]
    
    if sort_by:
        if sort_by == "due_date":
            filtered_tasks.sort(key=lambda task: task.due_date if task.due_date else "")
        elif sort_by == "created_at":
            filtered_tasks.sort(key=lambda task: task.created_at)
        elif sort_by == "title":
            filtered_tasks.sort(key=lambda task: task.title)
    
    start = (page - 1) * page_size
    end = start + page_size
    return filtered_tasks[start:end]

@app.get("/tasks/{task_id}")
async def read_task(task_id: int):
    task = tasks[task_id - 1] if task_id - 1 < len(tasks) else None
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}")
async def update_task(task_id: int, task: Task):
    if task_id - 1 >= len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    tasks[task_id - 1] = task
    return task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int):
    if task_id - 1 >= len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    del tasks[task_id - 1]
    return {"message": "Task deleted"}

@app.patch("/tasks/{task_id}/complete")
async def complete_task(task_id: int):
    if task_id - 1 >= len(tasks):
        raise HTTPException(status_code=404, detail="Task not found")
    tasks[task_id - 1].completed = True
    return tasks[task_id - 1]