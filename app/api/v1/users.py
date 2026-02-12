from fastapi import APIRouter, HTTPException
from utils.supabase_client import supabase

router = APIRouter()

@router.get("/profiles")
async def get_profiles():
    try:
        data = supabase.table("profiles").select("*").execute()
        return data.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
