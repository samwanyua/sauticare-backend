from pydantic import BaseModel
from typing import Optional

class LearnerDashboard(BaseModel):
    learner_id: int
    name: str
    accuracy: Optional[int]
    fluency: Optional[int]
    recent_feedback: Optional[str]

    class Config:
        orm_mode = True
