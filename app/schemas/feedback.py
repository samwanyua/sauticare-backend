from pydantic import BaseModel

class FeedbackBase(BaseModel):
    user_id: int
    lesson_id: str
    comment: str
    score: int = 0

class FeedbackCreate(FeedbackBase):
    pass

class FeedbackResponse(FeedbackBase):
    class Config:
        orm_mode = True
