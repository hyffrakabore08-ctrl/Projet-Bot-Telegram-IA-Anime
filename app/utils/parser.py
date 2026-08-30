import re

def clean_anime_title(text):
    """
    Clean anime title from episode numbers, quality tags, and other noise.
    Returns normalized title in uppercase.
    
    Examples:
        "Solo Leveling E01 HD" -> "SOLO LEVELING"
        "Attack on Titan Episode 12 1080p" -> "ATTACK ON TITAN"
        "Demon Slayer #5 [Sub]" -> "DEMON SLAYER"
    """
    if not text:
        return ""
    
    # Convert to uppercase
    text = text.upper()
    
    # Remove common quality tags
    quality_tags = [
        r'\s*HD\s*', r'\s*SD\s*', r'\s*1080P\s*', r'\s*720P\s*', 
        r'\s*4K\s*', r'\s*X264\s*', r'\s*X265\s*', r'\s*HEVC\s*',
        r'\s*AVC\s*', r'\s*BD\s*', r'\s*BLURAY\s*', r'\s*DUAL\s*'
    ]
    for tag in quality_tags:
        text = re.sub(tag, ' ', text)
    
    # Remove subtitle tags like [Sub], (VF), etc.
    text = re.sub(r'\s*\[.*?\]\s*', ' ', text)
    text = re.sub(r'\s*\(.*?\)\s*', ' ', text)
    
    # Remove episode patterns: E01, EP01, Episode 1, #1, etc.
    episode_patterns = [
        r'\s+E\d+\s*',           # E01, E1
        r'\s+EP\d+\s*',          # EP01, EP1
        r'\s+EPISODE\s+\d+\s*',  # Episode 1
        r'\s+#\d+\s*',           # #1
        r'\s+\d+\s*',            # Standalone numbers at end
    ]
    for pattern in episode_patterns:
        text = re.sub(pattern, ' ', text)
    
    # Remove special characters except spaces and letters
    text = re.sub(r'[^A-Z\s]', ' ', text)
    
    # Normalize spaces
    text = re.sub(r'\s+', ' ', text).strip()
    
    # Remove common suffix words
    suffix_words = ['THE ANIMATION', 'THE SERIES', 'ANIME', 'MANGA']
    for word in suffix_words:
        if text.endswith(word):
            text = text[:-len(word)].strip()
    
    return text


def extract_anime_titles_from_text(text):
    """
    Extract potential anime titles from a message text.
    Returns a list of cleaned titles.
    """
    if not text:
        return []
    
    # Split by common delimiters
    lines = re.split(r'[\n|•·▪▸►]', text)
    
    titles = []
    for line in lines:
        cleaned = clean_anime_title(line)
        if cleaned and len(cleaned) > 3:  # Minimum title length
            titles.append(cleaned)
    
    return titles


def normalize_username(username):
    """
    Normalize Telegram username (remove @ if present).
    """
    if not username:
        return ""
    return username.lstrip('@').lower()


def parse_user_message(message_text):
    """
    Parse user message to extract intent and parameters.
    Returns a dict with action and parameters.
    
    Supported actions:
        - ANALYZE_CHANNEL: Analyze a specific channel
        - GET_TOP_ANIMES: Get top animes from a channel
        - GET_STATS: Get statistics for a specific anime
        - UNKNOWN: Could not parse
    
    Examples:
        "VA SUR @MONCANAL ET DONNE MOI LE TOP 3 DES ANIMES"
        -> {action: GET_TOP_ANIMES, channel: @MONCANAL, count: 3}
        
        "ANALYSE LE CANAL 123456789"
        -> {action: ANALYZE_CHANNEL, channel_id: 123456789}
    """
    if not message_text:
        return {"action": "UNKNOWN", "params": {}}
    
    text = message_text.upper()
    
    result = {"action": "UNKNOWN", "params": {}}
    
    # Extract channel username or ID
    username_match = re.search(r'@(\w+)', text)
    id_match = re.search(r'\b(\d{8,15})\b', text)
    
    if username_match:
        result["params"]["username"] = username_match.group(1)
    elif id_match:
        result["params"]["channel_id"] = id_match.group(1)
    
    # Detect action
    if any(word in text for word in ["ANALYSE", "ANALYZE", "SCAN"]):
        result["action"] = "ANALYZE_CHANNEL"
    elif any(word in text for word in ["TOP", "MEILLEUR", "BEST"]):
        result["action"] = "GET_TOP_ANIMES"
        # Extract count (default 3)
        count_match = re.search(r'TOP\s+(\d+)', text)
        if count_match:
            result["params"]["count"] = int(count_match.group(1))
        else:
            result["params"]["count"] = 3
    elif any(word in text for word in ["STAT", "SCORE", "PERFORMANCE"]):
        result["action"] = "GET_STATS"
        # Try to extract anime name
        anime_match = re.search(r'(?:DE|D\'?|ABOUT)\s+([A-Z][A-Z\s]+?)(?:\s*$|\s+SUR|\s+POUR)', text)
        if anime_match:
            result["params"]["anime"] = anime_match.group(1).strip()
    else:
        # Default to analysis if a channel is mentioned
        if result["params"]:
            result["action"] = "ANALYZE_CHANNEL"
    
    return result
