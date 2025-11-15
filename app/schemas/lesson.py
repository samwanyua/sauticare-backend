from pydantic import BaseModel

class LessonBase(BaseModel):
    id: str
    level: str
    phrase: str

class LessonCreate(LessonBase):
    pass

class LessonResponse(LessonBase):
    class Config:
        orm_mode = True
