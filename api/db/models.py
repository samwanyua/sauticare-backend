from sqlalchemy import Column, Integer, String, Boolean, Text, ForeignKey
from sqlalchemy.orm import relationship
from db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # One-to-one relationship to profile
    profile = relationship("Profile", uselist=False, back_populates="user")


class Profile(Base):
    __tablename__ = "profiles"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), unique=True, nullable=False)
    preferred_name = Column(String(100), nullable=False)
    age = Column(Integer, nullable=True)
    bio = Column(Text, nullable=True)
    interests = Column(Text, nullable=True)  # comma-separated string
    location = Column(String(100), nullable=True)
    gender = Column(String(20), nullable=True)
    education_level = Column(String(50), nullable=True)

    user = relationship("User", back_populates="profile")


class Lesson(Base):
    __tablename__ = "lessons"
    id = Column(String, primary_key=True, index=True)
    level = Column(String, index=True)  # Easy / Medium / Hard
    phrase = Column(String)


class LessonProgress(Base):
    __tablename__ = "lesson_progress"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    lesson_id = Column(String)
    accuracy = Column(Integer)
    fluency = Column(Integer)
    timestamp = Column(String)


class Feedback(Base):
    __tablename__ = "feedback"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer)
    lesson_id = Column(String)
    comment = Column(String)
    score = Column(Integer, default=0)
