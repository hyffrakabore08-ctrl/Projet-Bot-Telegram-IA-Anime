from fastapi import FastAPI, APIRouter, HTTPException, Request, Form, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from datetime import datetime
import os
import json

from app.database import get_db_connection, init_db
from app.config import (
    TELEGRAM_BOT_TOKEN, HF_API_TOKEN, ADMIN_USER_ID,
    SCORE_WEIGHT_LIKES, SCORE_WEIGHT_VIEWS, SCORE_WEIGHT_COMMENTS,
    HF_MODEL_NAME, TIMEZONE, DEBUG_MODE
)
from app.bot.scheduler import PublicationScheduler
from app.bot.anilist_api import search_anime, get_upcoming_animes

# Router for API endpoints
router = APIRouter()

# Global scheduler instance
scheduler: Optional[PublicationScheduler] = None


class ChannelStatusUpdate(BaseModel):
    status: str


class SettingsUpdate(BaseModel):
    hf_model_name: str
    weight_likes: float
    weight_views: float
    weight_comments: float
    timezone: str
    debug_mode: int


@router.get("/")
async def root():
    """Serve the Mini App frontend."""
    return FileResponse("app/web/static/index.html")


@router.get("/api/channels")
async def get_channels():
    """Get all registered channels."""
    async with await get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM channels ORDER BY name")
        rows = await cursor.fetchall()
        columns = [description[0] for description in cursor.description]
        
        channels = []
        for row in rows:
            channel = dict(zip(columns, row))
            # Add mock data for demo
            channel["subscribers"] = channel.get("subscribers", 1000)
            channel["photo_url"] = channel.get("photo_url", "")
            channels.append(channel)
        
        return JSONResponse(content=channels)


@router.get("/api/channels/{channel_id}/details")
async def get_channel_details(channel_id: str):
    """Get detailed information about a specific channel."""
    async with await get_db_connection() as db:
        # Get channel info
        cursor = await db.execute(
            "SELECT * FROM channels WHERE telegram_id = ?", 
            (channel_id,)
        )
        row = await cursor.fetchone()
        
        if not row:
            raise HTTPException(status_code=404, detail="Channel not found")
        
        columns = [description[0] for description in cursor.description]
        channel = dict(zip(columns, row))
        
        # Mock subscriber history for chart
        subscriber_history = [
            {"date": "2024-01", "count": 950},
            {"date": "2024-02", "count": 980},
            {"date": "2024-03", "count": 1000},
            {"date": "2024-04", "count": 1050},
            {"date": "2024-05", "count": 1100},
        ]
        
        # Mock episodes
        episodes = [
            {"title": "SOLO LEVELING E01", "views": 5000, "likes": 450, "comments": 120},
            {"title": "SOLO LEVELING E02", "views": 4800, "likes": 430, "comments": 115},
            {"title": "SOLO LEVELING E03", "views": 5200, "likes": 480, "comments": 130},
        ]
        
        return JSONResponse(content={
            **channel,
            "subscriber_history": subscriber_history,
            "episodes": episodes
        })


@router.post("/api/channels/{channel_id}/status")
async def update_channel_status(channel_id: str, status_update: ChannelStatusUpdate):
    """Update channel status."""
    async with await get_db_connection() as db:
        await db.execute(
            "UPDATE channels SET status = ? WHERE telegram_id = ?",
            (status_update.status, channel_id)
        )
        await db.commit()
    
    return JSONResponse(content={"success": True, "status": status_update.status})


@router.get("/api/groups")
async def get_groups():
    """Get all linked groups with activity stats."""
    # Mock data - in production, fetch from database
    groups = [
        {
            "id": "123456789",
            "name": "ANIME FANS FRANCE",
            "members": 5420,
            "messages_per_day": 150,
            "activity_level": 75
        },
        {
            "id": "987654321",
            "name": "MANGA DISCUSSION",
            "members": 3200,
            "messages_per_day": 85,
            "activity_level": 45
        },
        {
            "id": "456789123",
            "name": "SORTIES ANIMÉ",
            "members": 8900,
            "messages_per_day": 220,
            "activity_level": 95
        }
    ]
    
    return JSONResponse(content=groups)


@router.get("/api/animes/upcoming")
async def get_upcoming_animes_endpoint():
    """Get upcoming animes from AniList."""
    try:
        # Get current season
        current_month = datetime.now().month
        if current_month in [1, 2, 3]:
            season = "WINTER"
            year = datetime.now().year
        elif current_month in [4, 5, 6]:
            season = "SPRING"
            year = datetime.now().year
        elif current_month in [7, 8, 9]:
            season = "SUMMER"
            year = datetime.now().year
        else:
            season = "FALL"
            year = datetime.now().year
        
        animes = await get_upcoming_animes(season=season, seasonYear=year, limit=10)
        
        # Format for frontend
        formatted_animes = []
        for anime in animes:
            title_data = anime.get("title", {})
            title = title_data.get("english") or title_data.get("romaji") or "TITRE INCONNU"
            
            # Format release date
            next_airing = anime.get("nextAiringEpisode", {})
            if next_airing and next_airing.get("airingAt"):
                airing_timestamp = next_airing["airingAt"]
                release_date = datetime.fromtimestamp(airing_timestamp).strftime("%d %B %Y")
            else:
                release_date = f"{season} {year}"
            
            formatted_animes.append({
                "title": title.upper(),
                "genres": anime.get("genres", []),
                "cover_image": anime.get("coverImage", {}).get("large", ""),
                "release_date": release_date.upper(),
                "average_score": anime.get("averageScore", 0)
            })
        
        return JSONResponse(content=formatted_animes)
    except Exception as e:
        print(f"Error fetching upcoming animes: {e}")
        return JSONResponse(content=[])


@router.post("/api/publish/direct")
async def publish_direct(
    content: str = Form(...),
    channels: str = Form(...),
    media: Optional[UploadFile] = File(None)
):
    """Publish content immediately to selected channels."""
    try:
        channel_ids = json.loads(channels)
        
        # In production, use Telegram bot to send messages
        # For now, just return success
        results = []
        for channel_id in channel_ids:
            results.append({
                "channel_id": channel_id,
                "success": True,
                "message": "Publication sent successfully"
            })
        
        return JSONResponse(content={
            "success": True,
            "results": results,
            "published_count": len(channel_ids)
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/api/publish/schedule")
async def publish_schedule(
    content: str = Form(...),
    channels: str = Form(...),
    scheduled_time: str = Form(...),
    repeat_type: str = Form("NONE"),
    repeat_interval: int = Form(0),
    media: Optional[UploadFile] = File(None)
):
    """Schedule a publication for later."""
    global scheduler
    
    try:
        channel_ids = json.loads(channels)
        scheduled_datetime = datetime.fromisoformat(scheduled_time.replace('Z', '+00:00'))
        
        # Store in database for each channel
        async with await get_db_connection() as db:
            for channel_id in channel_ids:
                await db.execute("""
                    INSERT INTO scheduled_posts 
                    (channel_id, content, scheduled_time, repeat_type, repeat_interval)
                    VALUES (?, ?, ?, ?, ?)
                """, (channel_id, content, scheduled_datetime, repeat_type, repeat_interval))
            
            await db.commit()
        
        # If scheduler is available, add jobs
        if scheduler:
            for channel_id in channel_ids:
                await scheduler.add_scheduled_post(
                    channel_id=channel_id,
                    content=content,
                    scheduled_time=scheduled_datetime,
                    repeat_type=repeat_type,
                    repeat_interval=repeat_interval
                )
        
        return JSONResponse(content={
            "success": True,
            "scheduled_count": len(channel_ids),
            "scheduled_time": scheduled_time
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/api/settings")
async def get_settings():
    """Get user settings."""
    async with await get_db_connection() as db:
        cursor = await db.execute("SELECT * FROM user_settings WHERE id = 1")
        row = await cursor.fetchone()
        
        if not row:
            # Return defaults
            return JSONResponse(content={
                "hf_model_name": HF_MODEL_NAME,
                "weight_likes": SCORE_WEIGHT_LIKES,
                "weight_views": SCORE_WEIGHT_VIEWS,
                "weight_comments": SCORE_WEIGHT_COMMENTS,
                "timezone": TIMEZONE,
                "debug_mode": DEBUG_MODE
            })
        
        columns = [description[0] for description in cursor.description]
        settings = dict(zip(columns, row))
        
        return JSONResponse(content=settings)


@router.post("/api/settings")
async def update_settings(settings_update: SettingsUpdate):
    """Update user settings."""
    async with await get_db_connection() as db:
        await db.execute("""
            UPDATE user_settings SET
                hf_model_name = ?,
                weight_likes = ?,
                weight_views = ?,
                weight_comments = ?,
                timezone = ?,
                debug_mode = ?
            WHERE id = 1
        """, (
            settings_update.hf_model_name,
            settings_update.weight_likes,
            settings_update.weight_views,
            settings_update.weight_comments,
            settings_update.timezone,
            settings_update.debug_mode
        ))
        await db.commit()
    
    return JSONResponse(content={"success": True})


def set_scheduler(sched: PublicationScheduler):
    """Set the global scheduler instance."""
    global scheduler
    scheduler = sched
