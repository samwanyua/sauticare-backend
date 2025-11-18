from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from api.db.database import get_db
from api.db.models import User, Profile, LessonProgress, Feedback
from api.schemas.dashboard import LearnerDashboard

router = APIRouter()

@router.get("/{learner_id}", response_model=LearnerDashboard)
def get_learner_dashboard(learner_id: int, db: Session = Depends(get_db)):
    # 1. Get user + profile
    user = db.query(User).filter(User.id == learner_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="Learner not found")

    profile = db.query(Profile).filter(Profile.user_id == learner_id).first()
    name = profile.preferred_name if profile else user.name

    # 2. Aggregate latest progress
    latest_progress = (
        db.query(LessonProgress)
        .filter(LessonProgress.user_id == learner_id)
        .order_by(LessonProgress.id.desc())
        .first()
    )

    # 3. Get latest feedback
    latest_feedback = (
        db.query(Feedback)
        .filter(Feedback.user_id == learner_id)
        .order_by(Feedback.id.desc())
        .first()
    )

    return LearnerDashboard(
        learner_id=learner_id,
        name=name,
        accuracy=latest_progress.accuracy if latest_progress else None,
        fluency=latest_progress.fluency if latest_progress else None,
        recent_feedback=latest_feedback.comment if latest_feedback else None,
    )
