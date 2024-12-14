from fastapi import FastAPI
from databases import Database
from main import Task

app = FastAPI()

database = Database("postgresql://user:password@host:port/dbname")

@app.on_event("startup")
async def database_connect():
    await database.connect()

@app.on_event("shutdown")
async def database_disconnect():
    await database.disconnect()

# Example of using the database to create a task
@app.post("/tasks/")
async def create_task(task: Task):
    query = "INSERT INTO tasks (title, description, due_date, tags, completed, created_at) VALUES (:title, :description, :due_date, :tags, :completed, :created_at) RETURNING *"
    values = task.dict()
    task_id = await database.execute(query, values)
    return task