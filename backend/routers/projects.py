from datetime import datetime, timezone
from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from core.db import get_db
from models import Log, Project
from schemas import ProjectCreate, ProjectRead, ProjectUpdate

router = APIRouter(prefix="/api/projects", tags=["projects"])


def build_response(data, error=None):
    return {
        "data": data,
        "error": error,
        "meta": {"timestamp": datetime.now(tz=timezone.utc).isoformat()},
    }


@router.get("/", response_model=dict)
def list_projects(db: Session = Depends(get_db)) -> dict:
    projects: List[Project] = db.query(Project).all()
    data = [ProjectRead.from_orm(project).dict() for project in projects]
    return build_response(data=data)


@router.get("/{project_id}", response_model=dict)
def get_project(project_id: UUID, db: Session = Depends(get_db)) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    data = ProjectRead.from_orm(project).dict()
    return build_response(data=data)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db)) -> dict:
    project = Project(**payload.dict())
    db.add(project)
    db.flush()

    log_entry = Log(
        actor_id=payload.created_by,
        action="create_project",
        target_table="projects",
        target_id=project.id,
        before_data=None,
        after_data=jsonable_encoder(ProjectRead.from_orm(project)),
    )
    db.add(log_entry)

    db.commit()
    db.refresh(project)
    data = ProjectRead.from_orm(project).dict()
    return build_response(data=data)


@router.put("/{project_id}", response_model=dict)
def update_project(project_id: UUID, payload: ProjectUpdate, db: Session = Depends(get_db)) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    before_state = jsonable_encoder(ProjectRead.from_orm(project))

    update_data = payload.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(project, key, value)

    log_entry = Log(
        actor_id=update_data.get("updated_by"),
        action="update_project",
        target_table="projects",
        target_id=project.id,
        before_data=before_state,
        after_data=None,  # will set after flush
    )
    db.add(log_entry)

    db.flush()
    db.refresh(project)
    log_entry.after_data = jsonable_encoder(ProjectRead.from_orm(project))

    db.commit()
    db.refresh(project)

    data = ProjectRead.from_orm(project).dict()
    return build_response(data=data)


