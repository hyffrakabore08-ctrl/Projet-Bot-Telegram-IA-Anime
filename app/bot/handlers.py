from telegram import Update
from telegram.ext import ContextTypes, MessageHandler, filters
from app.utils.parser import parse_user_message, clean_anime_title, extract_anime_titles_from_text
from app.bot.anilist_api import search_anime, get_upcoming_animes, format_anime_info
from app.bot.ia_agent import analyze_intent, generate_recommendation, format_bot_response
from app.config import ADMIN_USER_ID, SCORE_WEIGHT_LIKES, SCORE_WEIGHT_VIEWS, SCORE_WEIGHT_COMMENTS
import re


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle incoming private messages from the admin user.
    Analyzes intent and executes appropriate action.
    """
    user_id = update.effective_user.id
    
    # Restrict access to admin user only
    if ADMIN_USER_ID and user_id != ADMIN_USER_ID:
        await update.message.reply_text(
            "⛔ ACCÈS REFUSÉ. SEUL L'ADMINISTRATEUR PEUT UTILISER CE BOT."
        )
        return
    
    message_text = update.message.text
    
    if not message_text:
        return
    
    # Analyze intent using IA or fallback parser
    intent = await analyze_intent(message_text)
    
    # Also use local parser as backup
    local_parse = parse_user_message(message_text)
    
    # Merge results (local parser may have better channel extraction)
    if local_parse["params"].get("username") and not intent.get("params", {}).get("channel"):
        intent.setdefault("params", {})["channel"] = "@" + local_parse["params"]["username"]
    if local_parse["params"].get("channel_id") and not intent.get("params", {}).get("channel"):
        intent.setdefault("params", {})["channel"] = local_parse["params"]["channel_id"]
    if local_parse["action"] != "UNKNOWN" and intent.get("action") == "ANALYSE_CANAL":
        # Use local parser's action if more specific
        if local_parse["action"] in ["GET_TOP_ANIMES", "GET_STATS"]:
            intent["action"] = local_parse["action"]
            intent["params"]["count"] = local_parse["params"].get("count", 3)
    
    # Execute action based on detected intent
    if intent["action"] in ["ANALYSE_CANAL", "TOP_ANIMES"]:
        await handle_channel_analysis(update, context, intent)
    elif intent["action"] == "STATS_ANIME":
        await handle_anime_stats(update, context, intent)
    else:
        await update.message.reply_text(
            "🤔 JE N'AI PAS BIEN COMPRIS VOTRE DEMANDE.\n\n"
            "ESSAYEZ PAR EXEMPLE:\n"
            "- \"ANALYSE LE CANAL @MONCANAL\"\n"
            "- \"DONNE MOI LE TOP 3 DES ANIMES DE @MONCANAL\"\n"
            "- \"QUELLES SONT LES STATS DE SOLO LEVELING ?\""
        )


async def handle_channel_analysis(update: Update, context: ContextTypes.DEFAULT_TYPE, intent: dict):
    """
    Analyze a Telegram channel and return top animes.
    """
    channel = intent.get("params", {}).get("channel")
    count = intent.get("params", {}).get("count", 3)
    
    if not channel:
        await update.message.reply_text(
            "❌ VEUILLEZ SPÉCIFIER UN CANAL (EX: @MONCANAL OU L'ID DU CANAL)."
        )
        return
    
    # Send processing message
    processing_msg = await update.message.reply_text(
        f"🔍 ANALYSE EN COURS DU CANAL {channel.upper()}..."
    )
    
    try:
        # Get channel info
        if channel.startswith("@"):
            chat = await context.bot.get_chat(chat_id=channel)
        else:
            chat = await context.bot.get_chat(chat_id=channel)
        
        channel_name = chat.title or channel
        channel_username = chat.username or channel
        
        # Get recent messages from channel (limit to 100 for performance)
        messages = await context.bot.get_chat_history(
            chat_id=chat.id,
            limit=100
        )
        
        # Aggregate anime data
        anime_stats = {}
        
        async for msg in messages:
            # Get message text or caption
            text = msg.text or msg.caption
            if not text:
                continue
            
            # Extract potential anime titles
            titles = extract_anime_titles_from_text(text)
            
            for title in titles:
                if title not in anime_stats:
                    anime_stats[title] = {
                        "title": title,
                        "views": 0,
                        "likes": 0,
                        "comments": 0,
                        "message_count": 0
                    }
                
                # Accumulate stats
                anime_stats[title]["views"] += msg.views or 0
                anime_stats[title]["message_count"] += 1
                
                # Count reactions (likes)
                if msg.reactions:
                    for reaction in msg.reactions:
                        anime_stats[title]["likes"] += reaction.total_count or 0
        
        # Calculate scores and sort
        for title, stats in anime_stats.items():
            stats["score"] = (
                SCORE_WEIGHT_LIKES * stats["likes"] +
                SCORE_WEIGHT_VIEWS * stats["views"] +
                SCORE_WEIGHT_COMMENTS * stats["comments"]
            )
        
        # Sort by score and get top N
        sorted_animes = sorted(
            anime_stats.values(),
            key=lambda x: x["score"],
            reverse=True
        )[:count]
        
        # Enrich with AniList data
        enriched_animes = []
        for anime in sorted_animes:
            anilist_data = await search_anime(anime["title"])
            if anilist_data:
                anime["genres"] = anilist_data.get("genres", [])
                anime["anilist_info"] = anilist_data
            else:
                anime["genres"] = ["INCONNU"]
            enriched_animes.append(anime)
        
        # Generate IA recommendation based on #1
        recommendation = None
        if enriched_animes and enriched_animes[0].get("genres"):
            top_anime = enriched_animes[0]
            recommendation = await generate_recommendation(
                top_anime["genres"],
                top_anime["title"]
            )
        
        # Format response
        response = f"🏆 TOP {count} DES ANIMES DU CANAL @{channel_username or channel_name}\n\n"
        
        for i, anime in enumerate(enriched_animes, 1):
            response += f"{i}. {anime['title'].upper()}\n"
            response += f"   GENRE: {', '.join(anime.get('genres', [])).upper()}\n"
            response += f"   SCORE GLOBAL: {anime['score']:.0f}\n"
            response += f"   📊 LIKES: {anime['likes']} | VUES: {anime['views']} | MSG: {anime['message_count']}\n\n"
        
        if recommendation:
            response += f"\n🎯 RECOMMANDATION IA BASÉE SUR LE N°1:\n"
            response += f"   \"{recommendation.get('recommended_anime', 'INCONNU').upper()}\" "
            response += f"(PRÉVU POUR {recommendation.get('expected_date', 'N/A').upper()})\n"
            response += f"   GENRES SIMILAIRES: {', '.join(recommendation.get('genres', [])).upper()}\n"
        
        # Edit processing message with final result
        await processing_msg.edit_text(response)
        
        # Send cover image of #1 anime if available
        if enriched_animes and enriched_animes[0].get("anilist_info"):
            cover_url = enriched_animes[0]["anilist_info"].get("coverImage", {}).get("large")
            if cover_url:
                await update.message.reply_photo(
                    photo=cover_url,
                    caption=f"🎬 {enriched_animes[0]['title'].upper()}"
                )
    
    except Exception as e:
        await processing_msg.edit_text(
            f"❌ ERREUR LORS DE L'ANALYSE: {str(e).upper()}\n\n"
            f"ASSUREZ-VOUS QUE:\n"
            f"- LE BOT EST ADMIN DU CANAL\n"
            f"- LE CANAL EXISTE ET EST ACCESSIBLE"
        )


async def handle_anime_stats(update: Update, context: ContextTypes.DEFAULT_TYPE, intent: dict):
    """
    Get statistics for a specific anime across channels.
    """
    anime_name = intent.get("params", {}).get("anime")
    
    if not anime_name:
        await update.message.reply_text(
            "❌ VEUILLEZ SPÉCIFIER UN ANIME (EX: \"STATS DE SOLO LEVELING\")."
        )
        return
    
    # Search anime on AniList
    anilist_data = await search_anime(anime_name)
    
    if not anilist_data:
        await update.message.reply_text(
            f"❌ ANIME \"{anime_name.upper()}\" NON TROUVÉ SUR ANILIST."
        )
        return
    
    # Format and send stats
    formatted_info, cover_image = format_anime_info(anilist_data)
    
    if cover_image:
        await update.message.reply_photo(photo=cover_image, caption=formatted_info)
    else:
        await update.message.reply_text(formatted_info)
