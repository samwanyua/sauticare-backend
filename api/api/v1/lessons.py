# app/api/v1/lessons.py
from fastapi import APIRouter, Depends, HTTPException, status, Query
from api.utils.supabase_client import supabase
from api.dependencies import get_current_user, get_learner_profile
from api.schemas.lesson import LessonResponse, LessonWithPhrases, LessonProgressResponse
from typing import List, Optional

router = APIRouter(prefix="/lessons", tags=["lessons"])


@router.get("/", response_model=List[LessonResponse])
async def get_lessons(
    language: Optional[str] = Query(None, regex="^(en-KE|sw)$"),
    category: Optional[str] = Query(None, regex="^(nutrition|hygiene)$"),
    difficulty_level: Optional[int] = Query(None, ge=1, le=5),
    limit: int = Query(50, ge=1, le=100),
    current_user = Depends(get_current_user)
):
    """Get all lessons with optional filters"""
    try:
        query = supabase.table("lessons").select("*")
        
        if language:
            query = query.eq("language", language)
        if category:
            query = query.eq("category", category)
        if difficulty_level:
            query = query.eq("difficulty_level", difficulty_level)
        
        result = query.order("created_at", desc=True).limit(limit).execute()
        
        return result.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching lessons: {str(e)}"
        )


@router.get("/{lesson_id}", response_model=LessonWithPhrases)
async def get_lesson_detail(
    lesson_id: str,
    current_user = Depends(get_current_user)
):
    """Get lesson details with phrases"""
    try:
        # Get lesson
        lesson = supabase.table("lessons")\
            .select("*")\
            .eq("id", lesson_id)\
            .execute()
        
        if not lesson.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Lesson not found"
            )
        
        # Get phrases
        phrases = supabase.table("lesson_phrases")\
            .select("*")\
            .eq("lesson_id", lesson_id)\
            .order("sequence_order")\
            .execute()
        
        lesson_data = lesson.data[0]
        lesson_data["phrases"] = phrases.data
        
        return lesson_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching lesson: {str(e)}"
        )


@router.get("/progress/me", response_model=List[LessonProgressResponse])
async def get_my_progress(
    learner_profile = Depends(get_learner_profile)
):
    """Get lesson progress for current learner"""
    try:
        progress = supabase.table("lesson_progress")\
            .select("*")\
            .eq("learner_id", learner_profile["id"])\
            .order("started_at", desc=True)\
            .execute()
        
        return progress.data
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching progress: {str(e)}"
        )


@router.post("/progress/{lesson_id}/start")
async def start_lesson(
    lesson_id: str,
    learner_profile = Depends(get_learner_profile)
):
    """Start a lesson"""
    try:
        # Check if progress already exists
        existing = supabase.table("lesson_progress")\
            .select("*")\
            .eq("learner_id", learner_profile["id"])\
            .eq("lesson_id", lesson_id)\
            .execute()
        
        if existing.data:
            return {
                "message": "Lesson already started",
                "progress": existing.data[0]
            }
        
        # Create new progress
        progress_data = {
            "learner_id": learner_profile["id"],
            "lesson_id": lesson_id,
            "status": "in_progress",
            "completion_percentage": 0
        }
        
        result = supabase.table("lesson_progress").insert(progress_data).execute()
        
        return {
            "message": "Lesson started successfully",
            "progress": result.data[0]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error starting lesson: {str(e)}"
        )


@router.put("/progress/{lesson_id}/update")
async def update_lesson_progress(
    lesson_id: str,
    completion_percentage: float = Query(..., ge=0, le=100),
    learner_profile = Depends(get_learner_profile)
):
    """Update lesson progress"""
    try:
        status_value = "completed" if completion_percentage >= 100 else "in_progress"
        
        update_data = {
            "completion_percentage": completion_percentage,
            "status": status_value
        }
        
        if completion_percentage >= 100:
            from datetime import datetime
            update_data["completed_at"] = datetime.utcnow().isoformat()
        
        result = supabase.table("lesson_progress")\
            .update(update_data)\
            .eq("learner_id", learner_profile["id"])\
            .eq("lesson_id", lesson_id)\
            .execute()
        
        # Update analytics
        if completion_percentage >= 100:
            from datetime import date
            today = date.today().isoformat()
            
            analytics = supabase.table("learner_analytics")\
                .select("*")\
                .eq("learner_id", learner_profile["id"])\
                .eq("date", today)\
                .execute()
            
            if analytics.data:
                # Update existing
                current = analytics.data[0]
                supabase.table("learner_analytics")\
                    .update({"lessons_completed": current["lessons_completed"] + 1})\
                    .eq("id", current["id"])\
                    .execute()
            else:
                # Create new
                supabase.table("learner_analytics").insert({
                    "learner_id": learner_profile["id"],
                    "date": today,
                    "lessons_completed": 1
                }).execute()
        
        return {
            "message": "Progress updated successfully",
            "progress": result.data[0] if result.data else None
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error updating progress: {str(e)}"
        )