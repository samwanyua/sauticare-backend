# api/services/analytics_service.py
from typing import Dict, List, Optional
from datetime import datetime, timedelta, date
from api.utils.supabase_client import supabase
from fastapi import HTTPException


class AnalyticsService:
    """Service for handling analytics and statistics"""
    
    @staticmethod
    async def get_dashboard_analytics(learner_id: str, days: int = 7) -> Dict:
        """Get dashboard analytics for a learner"""
        try:
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
                sum(a["average_pronunciation_score"] * a["total_attempts"] 
                    for a in daily_analytics.data) / total_attempts
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
    
    @staticmethod
    async def get_progress_trend(learner_id: str, days: int = 30) -> Dict:
        """Get progress trend over time"""
        try:
            end_date = datetime.now().date()
            start_date = end_date - timedelta(days=days)
            
            analytics = supabase.table("learner_analytics")\
                .select("date", "average_pronunciation_score", "total_attempts", "successful_attempts")\
                .eq("learner_id", learner_id)\
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
    
    @staticmethod
    async def get_achievements(learner_id: str) -> Dict:
        """Get learner achievements and milestones"""
        try:
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
            
            # Calculate streak
            sorted_dates = sorted(
                [datetime.fromisoformat(a["date"]) for a in all_analytics.data], 
                reverse=True
            )
            current_streak = 0
            if sorted_dates:
                for i, date_obj in enumerate(sorted_dates):
                    expected_date = datetime.now().date() - timedelta(days=i)
                    if date_obj.date() == expected_date:
                        current_streak += 1
                    else:
                        break
            
            achievements = []
            
            # Define achievements
            if total_lessons >= 1:
                achievements.append({
                    "name": "First Steps",
                    "description": "Completed your first lesson",
                    "unlocked": True
                })
            if total_lessons >= 5:
                achievements.append({
                    "name": "Learning Journey",
                    "description": "Completed 5 lessons",
                    "unlocked": True
                })
            if total_lessons >= 10:
                achievements.append({
                    "name": "Dedicated Learner",
                    "description": "Completed 10 lessons",
                    "unlocked": True
                })
            
            if total_practice_minutes >= 60:
                achievements.append({
                    "name": "Practice Warrior",
                    "description": "Practiced for 1 hour",
                    "unlocked": True
                })
            if total_practice_minutes >= 300:
                achievements.append({
                    "name": "Time Master",
                    "description": "Practiced for 5 hours",
                    "unlocked": True
                })
            
            if current_streak >= 3:
                achievements.append({
                    "name": "Consistency King",
                    "description": "3-day practice streak",
                    "unlocked": True
                })
            if current_streak >= 7:
                achievements.append({
                    "name": "Week Warrior",
                    "description": "7-day practice streak",
                    "unlocked": True
                })
            
            if best_daily_score >= 85:
                achievements.append({
                    "name": "Excellence",
                    "description": "Scored 85+ average",
                    "unlocked": True
                })
            if best_daily_score >= 95:
                achievements.append({
                    "name": "Perfection",
                    "description": "Scored 95+ average",
                    "unlocked": True
                })
            
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
    
    @staticmethod
    async def update_daily_analytics(
        learner_id: str,
        practice_minutes: int = 0,
        lesson_completed: bool = False,
        attempt_score: Optional[float] = None,
        was_successful: bool = False
    ) -> Dict:
        """Update daily analytics for a learner"""
        try:
            today = date.today().isoformat()
            
            # Check if entry exists for today
            existing = supabase.table("learner_analytics")\
                .select("*")\
                .eq("learner_id", learner_id)\
                .eq("date", today)\
                .execute()
            
            if existing.data:
                # Update existing entry
                current = existing.data[0]
                new_total_attempts = current["total_attempts"] + (1 if attempt_score else 0)
                
                updated_data = {
                    "practice_time_minutes": current["practice_time_minutes"] + practice_minutes,
                    "lessons_completed": current["lessons_completed"] + (1 if lesson_completed else 0),
                    "total_attempts": new_total_attempts,
                    "successful_attempts": current["successful_attempts"] + (1 if was_successful else 0),
                }
                
                # Update average pronunciation score
                if attempt_score and new_total_attempts > 0:
                    updated_data["average_pronunciation_score"] = (
                        (current["average_pronunciation_score"] * current["total_attempts"] + attempt_score)
                        / new_total_attempts
                    )
                
                result = supabase.table("learner_analytics")\
                    .update(updated_data)\
                    .eq("id", current["id"])\
                    .execute()
            else:
                # Create new entry
                new_data = {
                    "learner_id": learner_id,
                    "date": today,
                    "practice_time_minutes": practice_minutes,
                    "lessons_completed": 1 if lesson_completed else 0,
                    "total_attempts": 1 if attempt_score else 0,
                    "successful_attempts": 1 if was_successful else 0,
                    "average_pronunciation_score": attempt_score or 0
                }
                
                result = supabase.table("learner_analytics")\
                    .insert(new_data)\
                    .execute()
            
            return result.data[0] if result.data else {}
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Error updating analytics: {str(e)}"
            )


# Singleton instance
analytics_service = AnalyticsService()