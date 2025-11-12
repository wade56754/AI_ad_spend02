from math import ceil
from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session

from backend.core.db import get_db
from backend.core.response import ok, paginated_response
from backend.core.security import AuthenticatedUser, get_current_user
from backend.models import Log, Project
from backend.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from backend.schemas.response import StandardResponse, ProjectListResponse

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("/", response_model=StandardResponse[ProjectListResponse])
def list_projects(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = Query(None),
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    query = db.query(Project)

    if status_filter:
        query = query.filter(Project.status == status_filter)

    if search:
        like_pattern = f"%{search}%"
        query = query.filter(Project.name.ilike(like_pattern))

    total = query.count()
    items: List[Project] = (
        query.order_by(Project.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    data = [ProjectRead.model_validate(project, from_attributes=True).model_dump() for project in items]
    return paginated_response(data=data, page=page, page_size=page_size, total=total)


@router.get("/{project_id}", response_model=StandardResponse[dict])
def get_project(
    project_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> JSONResponse:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    data = ProjectRead.model_validate(project, from_attributes=True).model_dump()
    return ok(data=data, status_code=status.HTTP_200_OK)


@router.post("/", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_project(
    payload: ProjectCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = Project(**payload.dict())
    db.add(project)
    db.flush()

    log_entry = Log(
        actor_id=payload.created_by,
        action="create_project",
        target_table="projects",
        target_id=project.id,
        before_data=None,
        after_data=jsonable_encoder(ProjectRead.model_validate(project, from_attributes=True).model_dump()),
    )
    db.add(log_entry)

    db.commit()
    db.refresh(project)
    data = ProjectRead.model_validate(project, from_attributes=True).model_dump()
    return ok(data=data)


@router.put("/{project_id}", response_model=dict)
def update_project(
    project_id: UUID,
    payload: ProjectUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> dict:
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    before_state = jsonable_encoder(ProjectRead.model_validate(project, from_attributes=True).model_dump())

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
    log_entry.after_data = jsonable_encoder(ProjectRead.model_validate(project, from_attributes=True).model_dump())

    db.commit()
    db.refresh(project)

    data = ProjectRead.model_validate(project, from_attributes=True).model_dump()
    return ok(data=data)


