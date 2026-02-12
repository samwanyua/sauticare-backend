# app/api/v1/analytics.py
from fastapi import APIRouter, Depends, HTTPException, Query
from api.utils.supabase_client import supabase
from api.dependencies import get_learner_profile, get_current_user
from typing import List, Dict, Any
from datetime import datetime, timedelta

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/dashboard")
async def get_dashboard_analytics(
    days: int = Query(7, ge=1, le=90),
    learner_profile = Depends(get_learner_profile)
):
    """Get dashboard analytics for learner"""
    try:
        learner_id = learner_profile["id"]
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        # Get daily analytics
        daily_analytics = supabase.table("learner_analytics")\
            .select("*")\
            .eq("learner_id", learner_id)\
            .gte("date", start_date.isoformat())\
            .lte("date", end_date.isoformat())\
            .order("date")\
            .execute()
        
        # Calculate summary stats
        total_practice_time = sum(a["practice_time_minutes"] for a in daily_analytics.data)
        total_lessons_completed = sum(a["lessons_completed"] for a in daily_analytics.data)
        total_attempts = sum(a["total_attempts"] for a in daily_analytics.data)
        total_successful = sum(a["successful_attempts"] for a in daily_analytics.data)
        
        avg_score = (
            sum(a["average_pronunciation_score"] * a["total_attempts"] for a in daily_analytics.data)
            / total_attempts
        ) if total_attempts > 0 else 0
        
        success_rate = (total_successful / total_attempts * 100) if total_attempts > 0 else 0
        
        # Get lesson progress summary
        lesson_progress = supabase.table("lesson_progress")\
            .select("status")\
            .eq("learner_id", learner_id)\
            .execute()
        
        progress_summary = {
            "completed": len([lp for lp in lesson_progress.data if lp["status"] == "completed"]),
            "in_progress": len([lp for lp in lesson_progress.data if lp["status"] == "in_progress"]),
            "not_started": len([lp for lp in lesson_progress.data if lp["status"] == "not_started"])
        }
        
        # Get recent practice sessions
        recent_sessions = supabase.table("practice_sessions")\
            .select("*")\
            .eq("learner_id", learner_id)\
            .order("started_at", desc=True)\
            .limit(5)\
            .execute()
        
        return {
            "summary": {
                "total_practice_time_minutes": total_practice_time,
                "total_lessons_completed": total_lessons_completed,
                "total_attempts": total_attempts,
                "successful_attempts": total_successful,
                "success_rate": round(success_rate, 2),
                "average_pronunciation_score": round(avg_score, 2),
                "days_analyzed": days
            },
            "daily_analytics": daily_analytics.data,
            "lesson_progress": progress_summary,
            "recent_sessions": recent_sessions.data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching analytics: {str(e)}"
        )


@router.get("/progress-trend")
async def get_progress_trend(
    days: int = Query(30, ge=7, le=90),
    learner_profile = Depends(get_learner_profile)
):
    """Get progress trend over time"""
    try:
        end_date = datetime.now().date()
        start_date = end_date - timedelta(days=days)
        
        analytics = supabase.table("learner_analytics")\
            .select("date", "average_pronunciation_score", "total_attempts", "successful_attempts")\
            .eq("learner_id", learner_profile["id"])\
            .gte("date", start_date.isoformat())\
            .lte("date", end_date.isoformat())\
            .order("date")\
            .execute()
        
        trend_data = []
        for item in analytics.data:
            success_rate = (
                (item["successful_attempts"] / item["total_attempts"] * 100)
                if item["total_attempts"] > 0 else 0
            )
            trend_data.append({
                "date": item["date"],
                "pronunciation_score": item["average_pronunciation_score"],
                "success_rate": round(success_rate, 2)
            })
        
        return {
            "period": f"{start_date} to {end_date}",
            "data": trend_data
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching trend: {str(e)}"
        )


@router.get("/achievements")
async def get_achievements(
    learner_profile = Depends(get_learner_profile)
):
    """Get learner achievements and milestones"""
    try:
        learner_id = learner_profile["id"]
        
        # Get total stats
        all_analytics = supabase.table("learner_analytics")\
            .select("*")\
            .eq("learner_id", learner_id)\
            .execute()
        
        total_lessons = sum(a["lessons_completed"] for a in all_analytics.data)
        total_practice_minutes = sum(a["practice_time_minutes"] for a in all_analytics.data)
        total_attempts = sum(a["total_attempts"] for a in all_analytics.data)
        
        # Get best scores
        best_daily_score = max(
            (a["average_pronunciation_score"] for a in all_analytics.data),
            default=0
        )
        
        # Get streak (consecutive days practiced)
        sorted_dates = sorted([datetime.fromisoformat(a["date"]) for a in all_analytics.data], reverse=True)
        current_streak = 0
        if sorted_dates:
            for i, date in enumerate(sorted_dates):
                expected_date = datetime.now().date() - timedelta(days=i)
                if date.date() == expected_date:
                    current_streak += 1
                else:
                    break
        
        achievements = []
        
        # Define achievements
        if total_lessons >= 1:
            achievements.append({"name": "First Steps", "description": "Completed your first lesson", "unlocked": True})
        if total_lessons >= 5:
            achievements.append({"name": "Learning Journey", "description": "Completed 5 lessons", "unlocked": True})
        if total_lessons >= 10:
            achievements.append({"name": "Dedicated Learner", "description": "Completed 10 lessons", "unlocked": True})
        
        if total_practice_minutes >= 60:
            achievements.append({"name": "Practice Warrior", "description": "Practiced for 1 hour", "unlocked": True})
        if total_practice_minutes >= 300:
            achievements.append({"name": "Time Master", "description": "Practiced for 5 hours", "unlocked": True})
        
        if current_streak >= 3:
            achievements.append({"name": "Consistency King", "description": "3-day practice streak", "unlocked": True})
        if current_streak >= 7:
            achievements.append({"name": "Week Warrior", "description": "7-day practice streak", "unlocked": True})
        
        if best_daily_score >= 85:
            achievements.append({"name": "Excellence", "description": "Scored 85+ average", "unlocked": True})
        if best_daily_score >= 95:
            achievements.append({"name": "Perfection", "description": "Scored 95+ average", "unlocked": True})
        
        return {
            "total_lessons_completed": total_lessons,
            "total_practice_minutes": total_practice_minutes,
            "total_attempts": total_attempts,
            "best_daily_score": round(best_daily_score, 2),
            "current_streak_days": current_streak,
            "achievements": achievements
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching achievements: {str(e)}"
        )