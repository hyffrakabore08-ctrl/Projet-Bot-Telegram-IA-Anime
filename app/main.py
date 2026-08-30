import asyncio
import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from telegram.ext import Application, MessageHandler, filters
from telegram import Update
import threading

from app.config import TELEGRAM_BOT_TOKEN, DATABASE_PATH, FASTAPI_HOST, FASTAPI_PORT
from app.database import init_db
from app.bot.handlers import handle_message
from app.bot.scheduler import PublicationScheduler
from app.web.routes import router, set_scheduler


# Create FastAPI app
app = FastAPI(title="Anime Manager Mini App", description="Telegram Bot + Mini App for Anime Management")

# Mount static files
app.mount("/static", StaticFiles(directory="app/web/static"), name="static")

# Include API routes
app.include_router(router)

# Global bot application instance
bot_app = None


def run_bot():
    """Run the Telegram bot in a separate thread."""
    global bot_app
    
    # Build bot application
    bot_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    
    # Add message handler for private messages
    bot_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    # Initialize scheduler
    scheduler = PublicationScheduler(bot_app)
    scheduler.start()
    
    # Set scheduler in web routes
    set_scheduler(scheduler)
    
    print("🤖 BOT TELEGRAM DÉMARRÉ EN MODE POLLING...")
    
    # Run bot (blocking call)
    bot_app.run_polling(allowed_updates=Update.ALL_TYPES)


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()
    print(f"💾 BASE DE DONNÉES INITIALISÉE: {DATABASE_PATH}")
    print(f"🌐 SERVEUR WEB DÉMARRÉ SUR http://{FASTAPI_HOST}:{FASTAPI_PORT}")


def main():
    """Main entry point - starts both bot and FastAPI server."""
    # Check if required environment variables are set
    if not TELEGRAM_BOT_TOKEN:
        print("⚠️  WARNING: TELEGRAM_BOT_TOKEN not set. Bot will not function.")
        print("   Please set TELEGRAM_BOT_TOKEN environment variable.")
    
    # Start bot in a separate thread
    if TELEGRAM_BOT_TOKEN:
        bot_thread = threading.Thread(target=run_bot, daemon=True)
        bot_thread.start()
        
        # Give bot time to initialize
        import time
        time.sleep(2)
    
    # Import uvicorn here to avoid issues
    import uvicorn
    
    # Run FastAPI server (main thread)
    print("\n🚀 DÉMARRAGE DU SERVEUR FASTAPI...")
    uvicorn.run(app, host=FASTAPI_HOST, port=FASTAPI_PORT)


if __name__ == "__main__":
    main()
