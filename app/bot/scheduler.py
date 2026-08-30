from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from apscheduler.triggers.interval import IntervalTrigger
from datetime import datetime
import aiosqlite
from app.database import get_db_connection
from app.config import TIMEZONE
from telegram.ext import Application


class PublicationScheduler:
    """
    Manage scheduled publications for Telegram channels.
    """
    
    def __init__(self, bot_application: Application):
        self.scheduler = AsyncIOScheduler(timezone=TIMEZONE)
        self.bot_app = bot_application
    
    async def add_scheduled_post(
        self,
        channel_id: str,
        content: str,
        media_url: str = None,
        scheduled_time: datetime = None,
        repeat_type: str = "NONE",
        repeat_interval: int = 0,
        repeat_count: int = 1
    ):
        """
        Add a scheduled post to the database and scheduler.
        """
        if not scheduled_time:
            scheduled_time = datetime.now()
        
        async with await get_db_connection() as db:
            await db.execute("""
                INSERT INTO scheduled_posts 
                (channel_id, content, media_url, scheduled_time, repeat_type, repeat_interval, repeat_count)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (channel_id, content, media_url, scheduled_time, repeat_type, repeat_interval, repeat_count))
            
            post_id = await db.execute("SELECT last_insert_rowid()")
            post_id = (await post_id.fetchone())[0]
            
            await db.commit()
        
        # Schedule the job
        self._schedule_job(post_id, channel_id, content, media_url, scheduled_time, repeat_type, repeat_interval)
        
        return post_id
    
    def _schedule_job(self, post_id: int, channel_id: str, content: str, media_url: str, 
                      scheduled_time: datetime, repeat_type: str, repeat_interval: int):
        """
        Schedule a job in APScheduler.
        """
        if repeat_type == "DAILY":
            trigger = CronTrigger(hour=scheduled_time.hour, minute=scheduled_time.minute)
        elif repeat_type == "WEEKLY":
            trigger = CronTrigger(
                hour=scheduled_time.hour, 
                minute=scheduled_time.minute,
                day_of_week=scheduled_time.strftime("%A")
            )
        elif repeat_type == "INTERVAL" and repeat_interval > 0:
            trigger = IntervalTrigger(hours=repeat_interval)
        else:
            # One-time execution
            trigger = None
        
        if trigger:
            self.scheduler.add_job(
                self._execute_post,
                trigger=trigger,
                args=[post_id, channel_id, content, media_url],
                id=f"post_{post_id}"
            )
        else:
            # Schedule one-time execution
            delay = (scheduled_time - datetime.now()).total_seconds()
            if delay > 0:
                self.scheduler.add_job(
                    self._execute_post,
                    trigger='date',
                    run_date=scheduled_time,
                    args=[post_id, channel_id, content, media_url],
                    id=f"post_{post_id}"
                )
    
    async def _execute_post(self, post_id: int, channel_id: str, content: str, media_url: str = None):
        """
        Execute a scheduled post.
        """
        try:
            if media_url:
                # Send photo
                await self.bot_app.bot.send_photo(
                    chat_id=channel_id,
                    photo=media_url,
                    caption=content
                )
            else:
                # Send text message
                await self.bot_app.bot.send_message(
                    chat_id=channel_id,
                    text=content
                )
            
            # Mark as executed in database
            async with await get_db_connection() as db:
                await db.execute("""
                    UPDATE scheduled_posts SET executed = 1 WHERE id = ?
                """, (post_id,))
                await db.commit()
            
            print(f"Post {post_id} executed successfully for channel {channel_id}")
        
        except Exception as e:
            print(f"Error executing post {post_id}: {e}")
    
    async def get_scheduled_posts(self, channel_id: str = None):
        """
        Get all scheduled posts, optionally filtered by channel.
        """
        async with await get_db_connection() as db:
            if channel_id:
                cursor = await db.execute("""
                    SELECT * FROM scheduled_posts 
                    WHERE channel_id = ? AND executed = 0
                    ORDER BY scheduled_time ASC
                """, (channel_id,))
            else:
                cursor = await db.execute("""
                    SELECT * FROM scheduled_posts 
                    WHERE executed = 0
                    ORDER BY scheduled_time ASC
                """)
            
            rows = await cursor.fetchall()
            columns = [description[0] for description in cursor.description]
            
            return [dict(zip(columns, row)) for row in rows]
    
    async def cancel_scheduled_post(self, post_id: int):
        """
        Cancel a scheduled post.
        """
        # Remove from scheduler
        try:
            self.scheduler.remove_job(f"post_{post_id}")
        except:
            pass
        
        # Mark as cancelled in database
        async with await get_db_connection() as db:
            await db.execute("""
                DELETE FROM scheduled_posts WHERE id = ?
            """, (post_id,))
            await db.commit()
    
    def start(self):
        """
        Start the scheduler.
        """
        self.scheduler.start()
        print("Publication scheduler started")
    
    def shutdown(self):
        """
        Shutdown the scheduler.
        """
        self.scheduler.shutdown()
