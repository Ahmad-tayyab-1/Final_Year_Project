from urllib.parse import parse_qs, urlparse


def extract_youtube_video_id(url: str):
    """Extract a YouTube video ID from common URL formats."""
    if not url:
        return None

    parsed = urlparse(url)
    host = parsed.netloc.lower()
    path_parts = [part for part in parsed.path.split("/") if part]

    if host.endswith("youtu.be") and path_parts:
        return _valid_video_id(path_parts[0])

    query_video_id = parse_qs(parsed.query).get("v", [None])[0]
    if query_video_id:
        return _valid_video_id(query_video_id)

    if host.endswith("youtube.com") and len(path_parts) >= 2:
        if path_parts[0] in {"embed", "shorts"}:
            return _valid_video_id(path_parts[1])

    return None


def _valid_video_id(video_id):
    if video_id and len(video_id) == 11:
        return video_id
    return None
