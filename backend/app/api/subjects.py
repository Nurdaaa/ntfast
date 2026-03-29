from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.core.database import get_db
from app.models.subject import Subject
from app.models.analysis import Analysis
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectUpdate, SubjectResponse
from app.services.auth_service import get_current_user

router = APIRouter()


def _check_subject_ownership(db: Session, subject_id: int, current_user: User) -> None:
    """Verify that the subject belongs to an analysis owned by current_user (or user is admin)."""
    if current_user.role == "admin":
        return
    owns = db.query(Analysis).filter(
        Analysis.analyst_id == current_user.id,
        Analysis.subject_id == subject_id,
    ).first()
    if not owns:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to access this subject",
        )


@router.get("/", response_model=List[SubjectResponse])
async def get_subjects(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    risk_level: Optional[int] = Query(None, ge=0, le=10),
    status: Optional[str] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get list of subjects with optional filters"""
    query = db.query(Subject)

    # Non-admin users can only see subjects linked to their own analyses
    if current_user.role != "admin":
        owned_subject_ids = db.query(Analysis.subject_id).filter(
            Analysis.analyst_id == current_user.id,
            Analysis.subject_id.isnot(None),
        ).distinct()
        query = query.filter(Subject.id.in_(owned_subject_ids))

    if risk_level:
        query = query.filter(Subject.risk_level == risk_level)
    if status:
        query = query.filter(Subject.status == status)
    if search:
        query = query.filter(
            (Subject.name.contains(search)) |
            (Subject.iin_bin.contains(search))
        )

    subjects = query.offset(skip).limit(limit).all()
    return subjects


@router.post("/", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
async def create_subject(
    subject: SubjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new subject"""
    # Check if IIN/BIN already exists
    existing = db.query(Subject).filter(Subject.iin_bin == subject.iin_bin).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Subject with this IIN/BIN already exists"
        )

    db_subject = Subject(**subject.model_dump())
    db.add(db_subject)
    db.commit()
    db.refresh(db_subject)
    return db_subject


@router.get("/{subject_id}", response_model=SubjectResponse)
async def get_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get subject by ID"""
    subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    _check_subject_ownership(db, subject_id, current_user)
    return subject


@router.put("/{subject_id}", response_model=SubjectResponse)
async def update_subject(
    subject_id: int,
    subject_update: SubjectUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Update subject"""
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    _check_subject_ownership(db, subject_id, current_user)

    update_data = subject_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_subject, field, value)

    db.commit()
    db.refresh(db_subject)
    return db_subject


@router.delete("/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_subject(
    subject_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Delete subject"""
    db_subject = db.query(Subject).filter(Subject.id == subject_id).first()
    if not db_subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found"
        )
    _check_subject_ownership(db, subject_id, current_user)

    db.delete(db_subject)
    db.commit()
    return None
