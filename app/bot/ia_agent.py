import httpx
from app.config import HF_API_TOKEN, HF_MODEL_NAME

async def analyze_intent(message_text):
    """
    Use Hugging Face LLM to analyze user message and extract intent.
    Returns a structured JSON with action and parameters.
    """
    prompt = f"""Tu es un assistant qui contrôle un bot Telegram spécialisé dans les animes.
À partir du message utilisateur ci-dessous, extrais une action parmi:
- ANALYSE_CANAL: Analyser un canal Telegram spécifique
- TOP_ANIMES: Obtenir le top des animes d'un canal
- STATS_ANIME: Obtenir les statistiques pour un anime spécifique
- PROGRAMMER_PUBLICATION: Programmer une publication
- RECOMMANDATION: Obtenir une recommandation d'anime

Retourne UNIQUEMENT un JSON valide avec cette structure:
{{
    "action": "ACTION_DETECTED",
    "params": {{
        "channel": "@username ou ID",
        "count": nombre_pour_top,
        "anime_name": "nom de l'anime si mentionné"
    }}
}}

Message utilisateur: "{message_text}"

JSON:"""

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 200,
            "temperature": 0.1,
            "return_full_text": False
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{HF_MODEL_NAME}/generate",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result[0].get("generated_text", "")
                
                # Try to parse JSON from response
                import json
                import re
                
                # Extract JSON from response
                json_match = re.search(r'\{[^}]*\}', generated_text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # Fallback: simple keyword matching
                text_upper = message_text.upper()
                if any(word in text_upper for word in ["ANALYSE", "SCAN"]):
                    return {"action": "ANALYSE_CANAL", "params": {}}
                elif "TOP" in text_upper:
                    return {"action": "TOP_ANIMES", "params": {"count": 3}}
                elif any(word in text_upper for word in ["STAT", "SCORE"]):
                    return {"action": "STATS_ANIME", "params": {}}
                else:
                    return {"action": "ANALYSE_CANAL", "params": {}}
    except Exception as e:
        print(f"IA Agent error: {e}")
        # Fallback to simple parsing
        return {"action": "ANALYSE_CANAL", "params": {}}


async def generate_recommendation(top_anime_genres, top_anime_title):
    """
    Generate an anime recommendation based on the top anime's genres.
    Uses Hugging Face LLM to suggest similar upcoming anime.
    """
    prompt = f"""Tu es un expert en animes. Basé sur l'anime populaire "{top_anime_title}" 
avec les genres: {', '.join(top_anime_genres)}.

Recommande UN SEUL anime similaire qui sortira prochainement (2025-2026).
Retourne UNIQUEMENT un JSON valide:
{{
    "recommended_anime": "TITRE DE L'ANIME",
    "reason": "Pourquoi cet anime est similaire",
    "expected_date": "MOIS ANNÉE",
    "genres": ["GENRE1", "GENRE2"]
}}

JSON:"""

    headers = {
        "Authorization": f"Bearer {HF_API_TOKEN}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "inputs": prompt,
        "parameters": {
            "max_new_tokens": 250,
            "temperature": 0.3,
            "return_full_text": False
        }
    }
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://api-inference.huggingface.co/models/{HF_MODEL_NAME}/generate",
                headers=headers,
                json=payload,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                generated_text = result[0].get("generated_text", "")
                
                import json
                import re
                
                json_match = re.search(r'\{[^}]*\}', generated_text, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
    except Exception as e:
        print(f"IA Recommendation error: {e}")
    
    return None


async def format_bot_response(action_result):
    """
    Format the bot response in UPPERCASE style.
    """
    if not action_result:
        return "DÉSOLÉ, JE N'AI PAS PU COMPRENDRE VOTRE DEMANDE."
    
    # Format based on action type
    if action_result.get("action") == "TOP_ANIMES":
        response = "🏆 TOP DES ANIMES DU CANAL\n\n"
        for i, anime in enumerate(action_result.get("animes", []), 1):
            response += f"{i}. {anime['title'].upper()}\n"
            response += f"   GENRE: {', '.join(anime.get('genres', [])).upper()}\n"
            response += f"   SCORE GLOBAL: {anime.get('score', 0):.0f}\n"
            response += f"   📊 LIKES: {anime.get('likes', 0)} | VUES: {anime.get('views', 0)} | COMMENTAIRES: {anime.get('comments', 0)}\n\n"
        
        if action_result.get("recommendation"):
            rec = action_result["recommendation"]
            response += f"\n🎯 RECOMMANDATION IA BASÉE SUR LE N°1:\n"
            response += f"   \"{rec.get('recommended_anime', 'INCONNU').upper()}\" (PRÉVU POUR {rec.get('expected_date', 'N/A').upper()})\n"
            response += f"   GENRES SIMILAIRES: {', '.join(rec.get('genres', [])).upper()}\n"
            response += f"   RAISON: {rec.get('reason', '').upper()}\n"
        
        return response
    
    elif action_result.get("action") == "ANALYSE_CANAL":
        return f"✅ ANALYSE DU CANAL TERMINÉE.\n\n{action_result.get('summary', 'RÉSUMAT NON DISPONIBLE').upper()}"
    
    elif action_result.get("action") == "STATS_ANIME":
        stats = action_result.get("stats", {})
        return f"📊 STATISTIQUES POUR {stats.get('title', 'INCONNU').upper()}\n\n" \
               f"VUES TOTALES: {stats.get('views', 0)}\n" \
               f"LIKES TOTAUX: {stats.get('likes', 0)}\n" \
               f"COMMENTAIRES: {stats.get('comments', 0)}\n" \
               f"SCORE GLOBAL: {stats.get('score', 0):.0f}"
    
    return "COMMANDE EXÉCUTÉE AVEC SUCCÈS."
