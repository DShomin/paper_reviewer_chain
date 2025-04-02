from googleapiclient.discovery import build


def search_youtube(query, api_key, max_results=5):
    # Build the YouTube service object
    youtube = build("youtube", "v3", developerKey=api_key)

    # Call the search.list method to retrieve results matching the specified query term
    search_response = (
        youtube.search()
        .list(q=query, part="snippet", maxResults=max_results, type="video")
        .execute()
    )

    video_ids = [
        item["id"]["videoId"]
        for item in search_response["items"]
        if item["id"]["kind"] == "youtube#video"
    ]

    # Call the videos.list method to retrieve detailed information about each video
    video_response = (
        youtube.videos()
        .list(id=",".join(video_ids), part="snippet,contentDetails,statistics")
        .execute()
    )

    videos = []
    for item in video_response["items"]:
        video_info = {
            "title": item["snippet"]["title"],
            "url": f"https://www.youtube.com/watch?v={item['id']}",
            "view_count": item["statistics"].get("viewCount", "N/A"),
            "like_count": item["statistics"].get("likeCount", "N/A"),
            "comment_count": item["statistics"].get("commentCount", "N/A"),
            "published_at": item["snippet"]["publishedAt"],
            "thumbnail_url": item["snippet"]["thumbnails"]["high"]["url"],
        }
        videos.append(video_info)

    return videos
