import os
import json
import sqlite3
from datetime import datetime, timedelta
import requests
import feedparser


class NewsDB:
    def __init__(self, db_path="portfolio.db"):
        self.db_path = db_path
        self.init_db()

    def init_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS news_cache (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                summary TEXT,
                source TEXT,
                source_type TEXT,
                url TEXT UNIQUE,
                thumbnail TEXT,
                category TEXT DEFAULT 'News',
                trending_score INTEGER DEFAULT 0,
                published_at TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_processed BOOLEAN DEFAULT FALSE
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS news_metadata (
                key TEXT PRIMARY KEY,
                value TEXT,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()
        conn.close()

    def insert_news(self, news_items):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        for item in news_items:
            try:
                c.execute(
                    """
                    INSERT OR REPLACE INTO news_cache 
                    (title, summary, source, source_type, url, thumbnail, category, trending_score, published_at, is_processed)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, TRUE)
                """,
                    (
                        item.get("title", ""),
                        item.get("summary", ""),
                        item.get("source", ""),
                        item.get("source_type", ""),
                        item.get("url", ""),
                        item.get("thumbnail", ""),
                        item.get("category", "News"),
                        item.get("trending_score", 0),
                        item.get("published_at", ""),
                    ),
                )
            except Exception as e:
                pass
        conn.commit()
        conn.close()

    def clear_processed(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("UPDATE news_cache SET is_processed = FALSE")
        conn.commit()
        conn.close()

    def set_last_update(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            INSERT OR REPLACE INTO news_metadata (key, value, updated_at)
            VALUES ('last_update', ?, CURRENT_TIMESTAMP)
        """,
            (datetime.now().isoformat(),),
        )
        conn.commit()
        conn.close()


db = NewsDB()


def get_tech_giant_blogs():
    return [
        ("OpenAI", "https://openai.com/blog/rss.xml"),
        ("Anthropic", "https://www.anthropic.com/news/rss"),
        ("Google AI", "https://blog.google/technology/ai/rss/"),
        ("Google DeepMind", "https://deepmind.google/blog/rss.xml"),
        ("Meta AI", "https://ai.meta.com/blog/"),
        ("Microsoft AI", "https://blogs.microsoft.com/ai/feed/"),
        ("Hugging Face", "https://huggingface.co/blog/feed.xml"),
    ]


def search_reddit(subreddit, query=""):
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {"q": query or "AI", "sort": "new", "limit": 25}
    try:
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for post in data["data"]["children"]:
                p = post["data"]
                preview = p.get("preview", {})
                images = preview.get("images", [{}])
                thumbnail = images[0].get("source", {}).get("url", "") if images else ""

                results.append(
                    {
                        "title": p.get("title", ""),
                        "summary": p.get("selftext", "")[:200]
                        if p.get("selftext")
                        else "",
                        "source": f"r/{subreddit}",
                        "source_type": "reddit",
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "thumbnail": thumbnail,
                        "category": categorize_post(p.get("title", "")),
                        "trending_score": p.get("score", 0) + p.get("num_comments", 0),
                        "published_at": datetime.fromtimestamp(
                            p.get("created_utc", 0)
                        ).isoformat()
                        if p.get("created_utc")
                        else "",
                    }
                )
            return results
    except Exception as e:
        print(f"Reddit error: {e}")
    return []


def search_hackernews(query="AI"):
    try:
        days_ago = int((datetime.now() - timedelta(days=7)).timestamp())
        url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&numericFilters=created_at_i>={days_ago}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for hit in data.get("hits", [])[:25]:
                obj_id = hit.get("objectID", "")
                results.append(
                    {
                        "title": hit.get("title", ""),
                        "summary": hit.get("excerpt", "")[:200]
                        if hit.get("excerpt")
                        else "",
                        "source": "Hacker News",
                        "source_type": "hackernews",
                        "url": hit.get(
                            "url", f"https://news.ycombinator.com/item?id={obj_id}"
                        ),
                        "thumbnail": "",
                        "category": categorize_post(hit.get("title", "")),
                        "trending_score": hit.get("points", 0)
                        + hit.get("num_comments", 0),
                        "published_at": datetime.fromtimestamp(
                            hit.get("created_at_i", 0)
                        ).isoformat()
                        if hit.get("created_at_i")
                        else "",
                    }
                )
            return results
    except Exception as e:
        print(f"HN error: {e}")
    return []


def search_youtube(api_key, query="AI news"):
    if not api_key:
        return []

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "relevance",
            "maxResults": 20,
            "key": api_key,
        }
        r = requests.get(url, params=params, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for item in data.get("items", []):
                vid = item["snippet"]
                results.append(
                    {
                        "title": vid.get("title", ""),
                        "summary": vid.get("description", "")[:200],
                        "source": vid.get("channelTitle", "YouTube"),
                        "source_type": "youtube",
                        "url": f"https://youtube.com/watch?v={item['id']['videoId']}",
                        "thumbnail": vid.get("thumbnails", {})
                        .get("high", {})
                        .get("url", ""),
                        "category": "Tutorial"
                        if any(
                            w in vid.get("title", "").lower()
                            for w in ["tutorial", "how", "guide"]
                        )
                        else "News",
                        "trending_score": 50,
                        "published_at": vid.get("publishedAt", ""),
                    }
                )
            return results
    except Exception as e:
        print(f"YouTube error: {e}")
    return []


def fetch_rss_feed(url, source_name):
    try:
        feed = feedparser.parse(url)
        results = []
        for entry in feed.entries[:15]:
            results.append(
                {
                    "title": entry.get("title", ""),
                    "summary": entry.get("summary", "")[:200]
                    if hasattr(entry, "summary")
                    else "",
                    "source": source_name,
                    "source_type": "blog",
                    "url": entry.get("link", ""),
                    "thumbnail": "",
                    "category": categorize_post(entry.get("title", "")),
                    "trending_score": 50,
                    "published_at": entry.get("published", "")
                    if hasattr(entry, "published")
                    else "",
                }
            )
        return results
    except Exception as e:
        print(f"RSS error for {source_name}: {e}")
    return []


def categorize_post(text):
    text_lower = text.lower()
    if any(
        k in text_lower
        for k in [
            "launch",
            "announce",
            "release",
            "introduce",
            "unveil",
            "debut",
            "new product",
            "new model",
        ]
    ):
        return "Launch"
    elif any(
        k in text_lower
        for k in [
            "research",
            "study",
            "paper",
            "arxiv",
            "findings",
            "discovery",
            "breakthrough",
        ]
    ):
        return "Research"
    elif any(
        k in text_lower
        for k in ["tutorial", "how to", "guide", "learn", "course", "lesson"]
    ):
        return "Tutorial"
    return "News"


def web_search_duckduckgo(query, max_results=10):
    try:
        from duckduckgo_search import DDGS

        results = []
        with DDGS() as ddgs:
            for r in ddgs.news(query, max_results=max_results):
                results.append(
                    {
                        "title": r.get("title", ""),
                        "summary": r.get("body", "")[:200],
                        "source": r.get("source", "Web"),
                        "source_type": "google",
                        "url": r.get("url", ""),
                        "thumbnail": "",
                        "category": categorize_post(r.get("title", "")),
                        "trending_score": 50,
                        "published_at": r.get("date", ""),
                    }
                )
        return results
    except Exception as e:
        print(f"DuckDuckGo error: {e}")
        return []


def deduplicate_news(news_list):
    seen_urls = set()
    seen_titles = set()
    unique = []
    for item in news_list:
        url = item.get("url", "").lower()
        title = item.get("title", "").lower()[:50]
        if url and url not in seen_urls and title not in seen_titles:
            seen_urls.add(url)
            seen_titles.add(title)
            unique.append(item)
    return unique


def filter_relevance(news_list):
    spam_keywords = ["casino", "gambling", "crypto scam", "free money"]
    filtered = []
    for item in news_list:
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        if not any(k in text for k in spam_keywords):
            if len(item.get("title", "")) > 10:
                filtered.append(item)
    return filtered


def rank_news(news_list):
    scored = []
    for item in news_list:
        score = item.get("trending_score", 0)
        title = item.get("title", "").lower()
        if any(w in title for w in ["launch", "announce", "release", "introduce"]):
            score += 20
        if "new" in title:
            score += 10
        if item.get("category") == "Launch":
            score += 15
        item["trending_score"] = score
        scored.append(item)
    return sorted(scored, key=lambda x: x["trending_score"], reverse=True)


def run_full_crew():
    print("Starting ahmadAI News Crew...")
    all_news = []

    print("1. Searching DuckDuckGo for AI news...")
    try:
        for query in [
            "AI tool launched 2025",
            "new artificial intelligence released",
            "AI startup funding announced",
        ]:
            all_news.extend(web_search_duckduckgo(query, 15))
    except Exception as e:
        print(f"DuckDuckGo error: {e}")

    print("2. Fetching Tech Giant blogs...")
    try:
        blogs = get_tech_giant_blogs()
        for source, url in blogs:
            all_news.extend(fetch_rss_feed(url, source))
    except Exception as e:
        print(f"Blogs error: {e}")

    print("3. Searching Reddit...")
    try:
        for sub in [
            "artificial",
            "MachineLearning",
            "technology",
            "ChatGPT",
            "singularity",
        ]:
            all_news.extend(search_reddit(sub, "AI"))
    except Exception as e:
        print(f"Reddit error: {e}")

    print("4. Searching YouTube...")
    try:
        api_key = os.environ.get("YOUTUBE_API_KEY", "")
        all_news.extend(search_youtube(api_key, "AI news today"))
    except Exception as e:
        print(f"YouTube error: {e}")

    print("5. Searching Hacker News...")
    try:
        all_news.extend(search_hackernews("AI"))
    except Exception as e:
        print(f"HN error: {e}")

    print(f"Total raw items: {len(all_news)}")

    print("6. Deduplicating...")
    all_news = deduplicate_news(all_news)
    print(f"After dedup: {len(all_news)}")

    print("7. Filtering relevance...")
    all_news = filter_relevance(all_news)

    print("8. Ranking...")
    all_news = rank_news(all_news)

    print("9. Storing in database...")
    db.clear_processed()
    db.insert_news(all_news)
    db.set_last_update()

    print(f"Done! Stored {len(all_news)} news items")
    return all_news


if __name__ == "__main__":
    run_full_crew()
