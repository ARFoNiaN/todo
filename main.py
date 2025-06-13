from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from uuid import UUID, uuid4
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title="Custom TODO API",
    description="Уникальное TODO-приложение с расширенными возможностями для управления задачами, проектами и пользователями",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://my-unique-frontend.com"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],
    allow_headers=["X-Custom-Header", "Content-Type"],
)


class TaskCreate(BaseModel):
    title: str = Field(..., description="Заголовок задачи")
    description: Optional[str] = Field(None, description="Описание задачи")
    completed: bool = Field(False, description="Статус выполнения")
    project_id: UUID = Field(..., description="ID связанного проекта")

class Task(TaskCreate):
    id: UUID = Field(default_factory=uuid4)

class ProjectCreate(BaseModel):
    name: str = Field(..., description="Название проекта")
    user_id: UUID = Field(..., description="ID владельца проекта")

class Project(ProjectCreate):
    id: UUID = Field(default_factory=uuid4)

class UserCreate(BaseModel):
    name: str = Field(..., description="Имя пользователя")

class User(UserCreate):
    id: UUID = Field(default_factory=uuid4)


class TaskRepository:
    def __init__(self):
        self._tasks: List[Task] = []

    def get_all(self): return self._tasks

    def find_by_id(self, task_id: UUID) -> Optional[Task]:
        return next((task for task in self._tasks if task.id == task_id), None)

    def add_task(self, task_data: TaskCreate) -> Task:
        new_task = Task(**task_data.dict())
        self._tasks.append(new_task)
        print(f"Добавлена задача {new_task.id} по проекту {new_task.project_id}")
        return new_task

    def modify_task(self, task_id: UUID, updated_task: Task) -> Optional[Task]:
        for idx, task in enumerate(self._tasks):
            if task.id == task_id:
                self._tasks[idx] = updated_task
                print(f"Обновлена задача {task_id}")
                return updated_task
        return None

    def remove_task(self, task_id: UUID) -> bool:
        for idx, task in enumerate(self._tasks):
            if task.id == task_id:
                del self._tasks[idx]
                print(f"Удалена задача {task_id}")
                return True
        return False

class ProjectRepository:
    def __init__(self):
        self._projects: List[Project] = []

    def list_projects(self): return self._projects

    def create_project(self, project_data: ProjectCreate) -> Project:
        project = Project(**project_data.dict())
        self._projects.append(project)
        print(f"Создан проект {project.id} для пользователя {project.user_id}")
        return project

class UserRepository:
    def __init__(self):
        self._users: List[User] = []

    def get_users(self): return self._users

    def add_user(self, user_data: UserCreate) -> User:
        user = User(**user_data.dict())
        self._users.append(user)
        print(f"Добавлен пользователь {user.name} с ID {user.id}")
        return user


task_repo = TaskRepository()
project_repo = ProjectRepository()
user_repo = UserRepository()


@app.get("/tasks", response_model=List[Task], tags=["Tasks"])
def fetch_tasks(project_id: Optional[UUID] = Query(None)):
    tasks = task_repo.get_all()
    if project_id:
        tasks_filtered = [t for t in tasks if t.project_id == project_id]
        print(f"Фильтрация задач по проекту {project_id}: найдено {len(tasks_filtered)} задач")
        return tasks_filtered
    print("Получен полный список задач")
    return tasks

@app.post("/tasks", response_model=Task, tags=["Tasks"])
def create_new_task(task_data: TaskCreate):

    if not any(p.id == task_data.project_id for p in project_repo.list_projects()):
        raise HTTPException(status_code=400, detail="Проект не найден")
    
    new_task = task_repo.add_task(task_data)
    

    return new_task

@app.get("/tasks/{task_id}", response_model=Task)
def get_single_task(task_id: UUID):
    task = task_repo.find_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Задача не найдена")
    

    return task

@app.put("/tasks/{task_id}", response_model=Task)
def update_existing_task(task_id: UUID, updated_task: Task):
    if not any(p.id == updated_task.project_id for p in project_repo.list_projects()):
        raise HTTPException(status_code=400, detail="Проект не найден")
    
    result = task_repo.modify_task(task_id, updated_task)
    
    if not result:
        raise HTTPException(status_code=404, detail="Задача не найдена для обновления")
    

    
@app.delete("/tasks/{task_id}")
def delete_existing_task(task_id: UUID):
    success = task_repo.remove_task(task_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Задача не найдена для удаления")
    

@app.get("/projects", response_model=List[Project], tags=["Projects"])
def fetch_projects(user_id: Optional[UUID] = Query(None)):
    projects = project_repo.list_projects()
    
    if user_id:
        filtered_projects = [p for p in projects if p.user_id == user_id]
        print(f"Фильтрация проектов по пользователю {user_id}: найдено {len(filtered_projects)} проектов")
        return filtered_projects
    

@app.post("/projects", response_model=Project)
def create_new_project(project_data: ProjectCreate):
     if not any(u.id == project_data.user_id for u in user_repo.get_users()):
         raise HTTPException(status_code=400, detail="Пользователь не найден")
     
     new_project = project_repo.create_project(project_data)
     print(f"Создан новый проект {new_project.id} для пользователя {new_project.user_id}")
     return new_project

@app.get("/users", response_model=List[User])
def list_users():
     users_list = user_repo.get_users()
     print(f"Получено {len(users_list)} пользователей")
     return users_list

@app.post("/users", response_model=User)
def add_user(user_data: UserCreate):
     new_user = user_repo.add_user(user_data)
     print(f"Добавлен пользователь {new_user.name} с ID {new_user.id}")
     return new_user