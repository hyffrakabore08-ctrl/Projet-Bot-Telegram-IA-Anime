import aiosqlite
from datetime import datetime
import os
from app.config import DATABASE_PATH

async def init_db():
    """Initialize SQLite database with required tables."""
    # Ensure data directory exists
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    async with aiosqlite.connect(DATABASE_PATH) as db:
        # Channels table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS channels (
                id INTEGER PRIMARY KEY,
                telegram_id TEXT UNIQUE NOT NULL,
                name TEXT,
                username TEXT,
                status TEXT DEFAULT 'ACTIVE',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Posts table (cached analysis results)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                anime_title TEXT NOT NULL,
                message_id INTEGER,
                views INTEGER DEFAULT 0,
                likes INTEGER DEFAULT 0,
                comments INTEGER DEFAULT 0,
                score REAL DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(telegram_id)
            )
        """)
        
        # Scheduled publications table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS scheduled_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                channel_id TEXT NOT NULL,
                content TEXT,
                media_url TEXT,
                scheduled_time TIMESTAMP NOT NULL,
                repeat_type TEXT DEFAULT 'NONE',
                repeat_interval INTEGER DEFAULT 0,
                repeat_count INTEGER DEFAULT 1,
                executed INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (channel_id) REFERENCES channels(telegram_id)
            )
        """)
        
        # Anime recommendations table (validated by user)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS recommendations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                anime_title TEXT NOT NULL,
                anilist_id INTEGER,
                genres TEXT,
                release_date TEXT,
                cover_image TEXT,
                synopsis TEXT,
                target_channel TEXT,
                validated INTEGER DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # User settings table
        await db.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY,
                hf_model_name TEXT DEFAULT 'mistralai/Mistral-7B-Instruct-v0.2',
                weight_likes REAL DEFAULT 0.5,
                weight_views REAL DEFAULT 0.3,
                weight_comments REAL DEFAULT 0.2,
                timezone TEXT DEFAULT 'UTC',
                debug_mode INTEGER DEFAULT 0
            )
        """)
        
        # Insert default settings if not exists
        await db.execute("""
            INSERT OR IGNORE INTO user_settings (id, hf_model_name, weight_likes, weight_views, weight_comments, timezone, debug_mode)
            VALUES (1, 'mistralai/Mistral-7B-Instruct-v0.2', 0.5, 0.3, 0.2, 'UTC', 0)
        """)
        
        await db.commit()
    
    print(f"Database initialized at {DATABASE_PATH}")

async def get_db_connection():
    """Get a database connection."""
    return await aiosqlite.connect(DATABASE_PATH)
