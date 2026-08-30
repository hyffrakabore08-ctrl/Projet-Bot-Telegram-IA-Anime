import httpx
from app.config import ANILIST_API_URL

async def search_anime(search_query):
    """
    Search for an anime on AniList by title.
    Returns anime data or None if not found.
    """
    query = """
    query ($search: String) {
        Media(search: $search, type: ANIME) {
            id
            title {
                romaji
                english
                native
            }
            genres
            description(asHtml: false)
            coverImage {
                large
                medium
            }
            seasonYear
            averageScore
            status
            episodes
            nextAiringEpisode {
                episode
                airingAt
                timeUntilAiring
            }
        }
    }
    """
    
    variables = {"search": search_query}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANILIST_API_URL,
            json={"query": query, "variables": variables},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and data["data"].get("Media"):
                return data["data"]["Media"]
    
    return None


async def get_upcoming_animes(genres=None, season=None, seasonYear=None, limit=10):
    """
    Get upcoming animes from AniList.
    Optionally filter by genres and season.
    """
    query = """
    query ($genres: [String], $season: MediaSeason, $seasonYear: Int, $limit: Int) {
        Page(perPage: $limit) {
            media (
                type: ANIME,
                season: $season,
                seasonYear: $seasonYear,
                genre_in: $genres,
                sort: POPULARITY_DESC
            ) {
                id
                title {
                    romaji
                    english
                }
                genres
                description(asHtml: false)
                coverImage {
                    large
                }
                seasonYear
                averageScore
                nextAiringEpisode {
                    episode
                    airingAt
                    timeUntilAiring
                }
            }
        }
    }
    """
    
    variables = {
        "limit": limit,
        "season": season,
        "seasonYear": seasonYear
    }
    
    if genres:
        variables["genres"] = genres
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANILIST_API_URL,
            json={"query": query, "variables": variables},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and data["data"].get("Page"):
                return data["data"]["Page"]["media"]
    
    return []


async def get_anime_by_id(anime_id):
    """
    Get anime details by AniList ID.
    """
    query = """
    query ($id: Int) {
        Media(id: $id, type: ANIME) {
            id
            title {
                romaji
                english
                native
            }
            genres
            description(asHtml: false)
            coverImage {
                large
                medium
            }
            seasonYear
            averageScore
            status
            episodes
            bannerImage
        }
    }
    """
    
    variables = {"id": anime_id}
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            ANILIST_API_URL,
            json={"query": query, "variables": variables},
            timeout=10.0
        )
        
        if response.status_code == 200:
            data = response.json()
            if data.get("data") and data["data"].get("Media"):
                return data["data"]["Media"]
    
    return None


def format_anime_info(anime_data):
    """
    Format anime data for display in Telegram messages.
    Returns formatted string in UPPERCASE.
    """
    if not anime_data:
        return "ANIME NON TROUVÉ"
    
    title = anime_data.get("title", {})
    title_text = title.get("english") or title.get("romaji") or "TITRE INCONNU"
    
    genres = ", ".join(anime_data.get("genres", [])) if anime_data.get("genres") else "GENRES INCONNUS"
    
    description = anime_data.get("description", "PAS DE SYNOPSIS DISPONIBLE")
    if description and len(description) > 500:
        description = description[:500] + "..."
    
    score = anime_data.get("averageScore", "N/A")
    year = anime_data.get("seasonYear", "N/A")
    episodes = anime_data.get("episodes", "N/A")
    status = anime_data.get("status", "INCONNU")
    
    cover_image = anime_data.get("coverImage", {}).get("large", "")
    
    formatted = f"""🎬 {title_text.upper()}

📊 SCORE MOYEN: {score}/100
📅 ANNÉE: {year}
🎭 GENRES: {genres.upper()}
📺 ÉPISODES: {episodes}
🔘 STATUT: {status.upper()}

📝 SYNOPSIS:
{description.upper()}
"""
    
    return formatted, cover_image
