from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Enum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from typing import List, Optional

# Database setup
SQLALCHEMY_DATABASE_URL = "postgresql://user:password@host:port/dbname"
engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Task(Base):
    __tablename__ = "tasks"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, index=True)
    description = Column(String)
    due_date = Column(DateTime, nullable=True)
    tags = Column(String, nullable=True)
    completed = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

Base.metadata.create_all(bind=engine)

class TaskBase(BaseModel):
    title: str
    description: str
    due_date: Optional[datetime]
    tags: Optional[List[str]]

class TaskCreate(TaskBase):
    pass

class TaskUpdate(TaskBase):
    completed: Optional[bool]

class TaskResponse(TaskBase):
    id: int
    completed: bool
    created_at: datetime

    class Config:
        orm_mode = True

app = FastAPI()

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
        
# Routes
@app.post("/tasks/", response_model=TaskResponse)
async def create_task(task: TaskCreate, db: SessionLocal = Depends(get_db)):
    db_task = Task(**task.dict())
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.get("/tasks/", response_model=List[TaskResponse])
async def read_tasks(db: SessionLocal = Depends(get_db), tags: Optional[List[str]] = None, completed: Optional[bool] = None, sort_by: Optional[str] = None, page: int = 1, page_size: int = 10):
    query = db.query(Task)
    if tags:
        query = query.filter(Task.tags.in_(tags))
    if completed is not None:
        query = query.filter(Task.completed == completed)
    if sort_by:
        if sort_by == "due_date":
            query = query.order_by(Task.due_date)
        elif sort_by == "created_at":
            query = query.order_by(Task.created_at)
        elif sort_by == "title":
            query = query.order_by(Task.title)
    offset = (page - 1) * page_size
    tasks = query.offset(offset).limit(page_size).all()
    return tasks

@app.get("/tasks/{task_id}", response_model=TaskResponse)
async def read_task(task_id: int, db: SessionLocal = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task

@app.put("/tasks/{task_id}", response_model=TaskResponse)
async def update_task(task_id: int, task: TaskUpdate, db: SessionLocal = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if not db_task:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = task.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_task, key, value)
    db.commit()
    db.refresh(db_task)
    return db_task

@app.delete("/tasks/{task_id}")
async def delete_task(task_id: int, db: SessionLocal = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(task)
    db.commit()
    return JSONResponse(content={"message": "Task deleted"}, status_code=200)

@app.patch("/tasks/{task_id}/complete")
async def complete_task(task_id: int, db: SessionLocal = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = True
    db.commit()
    db.refresh(task)
    return task