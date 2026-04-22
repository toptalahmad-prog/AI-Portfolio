import os
import json
import sqlite3
from datetime import datetime, timedelta
from crewai import Agent, Task, Crew, Process
from crewai_tools import DuckDuckGoSearchTool, RSSFeedTool
import requests
import feedparser

duck_search = DuckDuckGoSearchTool()


class Database:
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
                category TEXT,
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
                    (title, summary, source, source_type, url, thumbnail, category, trending_score, published_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                print(f"Insert error: {e}")
        conn.commit()
        conn.close()

    def get_news(self, limit=50, category=None, source_type=None):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()

        query = "SELECT * FROM news_cache WHERE is_processed = TRUE"
        params = []

        if category and category != "all":
            query += " AND category = ?"
            params.append(category)

        if source_type and source_type != "all":
            query += " AND source_type = ?"
            params.append(source_type)

        query += " ORDER BY trending_score DESC, created_at DESC LIMIT ?"
        params.append(limit)

        c.execute(query, params)
        rows = c.fetchall()
        conn.close()

        columns = [
            "id",
            "title",
            "summary",
            "source",
            "source_type",
            "url",
            "thumbnail",
            "category",
            "trending_score",
            "published_at",
            "created_at",
            "is_processed",
        ]

        return [dict(zip(columns, row)) for row in rows]

    def mark_processed(self, count=100):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute(
            """
            UPDATE news_cache SET is_processed = TRUE
            WHERE id IN (SELECT id FROM news_cache WHERE is_processed = FALSE ORDER BY trending_score DESC LIMIT ?)
        """,
            (count,),
        )
        conn.commit()
        conn.close()

    def clear_old_news(self, hours=72):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        cutoff = (datetime.now() - timedelta(hours=hours)).strftime("%Y-%m-%d %H:%M:%S")
        c.execute("DELETE FROM news_cache WHERE created_at < ?", (cutoff,))
        conn.commit()
        conn.close()

    def get_last_update(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute("SELECT value FROM news_metadata WHERE key = 'last_update'")
        row = c.fetchone()
        conn.close()
        return row[0] if row else None

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


db = Database()


def get_tech_giant_blogs():
    return {
        "OpenAI": "https://openai.com/blog/rss.xml",
        "Anthropic": "https://www.anthropic.com/news/rss",
        "Google AI": "https://blog.google/technology/ai/rss/",
        "Google DeepMind": "https://deepmind.google/blog/rss.xml",
        "Meta AI": "https://ai.meta.com/blog/",
        "Microsoft AI": "https://blogs.microsoft.com/ai/feed/",
        "xAI": "https://x.ai/blog",
        "Mistral AI": "https://mistral.ai/news/",
        "Cohere": "https://cohere.com/blog/rss.xml",
        "Amazon AI": "https://aws.amazon.com/blogs/machine-learning/feed/",
        "Apple ML": "https://machinelearning.apple.com/feed.xml",
        "Nvidia AI": "https://blogs.nvidia.com/blog/category/deep-learning/feed/",
        "Stability AI": "https://stability.ai/newsroom",
        "Hugging Face": "https://huggingface.co/blog/feed.xml",
        "Midjourney": "https://www.midjourney.com/news",
        "Salesforce AI": "https://www.salesforce.com/news/",
        "Adobe AI": "https://blog.adobe.com/topics/artificial-intelligence.rss",
        "Samsung AI": "https://research.samsung.com/blog",
        "Tesla AI": "https://tesla-cdn.thron.io/publications/",
        "Cohere": "https://cohere.com/blog/rss.xml",
    }


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
                results.append(
                    {
                        "title": p.get("title", ""),
                        "summary": p.get("selftext", "")[:200]
                        if p.get("selftext")
                        else "",
                        "source": f"r/{subreddit}",
                        "source_type": "reddit",
                        "url": f"https://reddit.com{p.get('permalink', '')}",
                        "thumbnail": p.get("preview", {})
                        .get("images", [{}])[0]
                        .get("source", {})
                        .get("url", "")
                        if p.get("preview")
                        else "",
                        "category": categorize_post(
                            p.get("title", "") + " " + p.get("selftext", "")
                        ),
                        "trending_score": p.get("score", 0) + p.get("num_comments", 0),
                        "published_at": datetime.fromtimestamp(
                            p.get("created_utc", 0)
                        ).isoformat(),
                    }
                )
            return results
    except Exception as e:
        print(f"Reddit error: {e}")
    return []


def search_hackernews(query="AI"):
    try:
        url = f"https://hn.algolia.com/api/v1/search?query={query}&tags=story&numericFilters=created_at_i>={int((datetime.now() - timedelta(days=7)).timestamp())}"
        r = requests.get(url, timeout=10)
        if r.status_code == 200:
            data = r.json()
            results = []
            for hit in data.get("hits", [])[:25]:
                results.append(
                    {
                        "title": hit.get("title", ""),
                        "summary": hit.get("excerpt", "")[:200]
                        if hit.get("excerpt")
                        else "",
                        "source": "Hacker News",
                        "source_type": "hackernews",
                        "url": hit.get(
                            "url",
                            f"https://news.ycombinator.com/item?id={hit.get('objectID')}",
                        ),
                        "thumbnail": "",
                        "category": categorize_post(
                            hit.get("title", "") + " " + hit.get("excerpt", "")
                        ),
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
        return search_youtube_no_api()

    try:
        url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "relevance",
            "maxResults": 25,
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


def search_youtube_no_api():
    try:
        url = "https://www.youtube.com/results"
        params = {"search_query": "AI news today artificial intelligence"}
        r = requests.get(url, timeout=10)
    except Exception as e:
        print(f"YouTube scrap error: {e}")
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
                    if entry.get("summary")
                    else "",
                    "source": source_name,
                    "source_type": "blog",
                    "url": entry.get("link", ""),
                    "thumbnail": "",
                    "category": categorize_post(
                        entry.get("title", "") + " " + entry.get("summary", "")
                    ),
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
    launch_keywords = [
        "launch",
        "announce",
        "release",
        "introduce",
        "unveil",
        "debut",
        "new product",
        "new model",
    ]
    research_keywords = [
        "research",
        "study",
        "paper",
        "arxiv",
        "findings",
        "discovery",
        "breakthrough",
    ]
    tutorial_keywords = ["tutorial", "how to", "guide", "learn", "course", "lesson"]

    if any(k in text_lower for k in launch_keywords):
        return "Launch"
    elif any(k in text_lower for k in research_keywords):
        return "Research"
    elif any(k in text_lower for k in tutorial_keywords):
        return "Tutorial"
    return "News"


researcher_google = Agent(
    role="Google AI Scanner",
    goal="Find all new AI launches and products using comprehensive web search",
    backstory="""You are an expert at finding newly launched AI products and tools.
    You search the web using multiple search terms to catch any new AI that just launched.
    You focus on finding fresh content about AI tools, platforms, and products.""",
    tools=[duck_search],
    verbose=True,
)

researcher_tech_giants = Agent(
    role="Tech Giants Monitor",
    goal="Monitor all major AI companies for news and announcements",
    backstory="""You monitor AI news from all major tech companies including:
    OpenAI, Anthropic, Google, Meta, Microsoft, xAI, Mistral, Cohere, 
    Amazon, Apple, Nvidia, Stability AI, Hugging Face, Midjourney, and more.
    You check their official blogs, news sections, and announcement pages.""",
    tools=[duck_search],
    verbose=True,
)

researcher_reddit = Agent(
    role="Reddit AI News Researcher",
    goal="Find trending AI discussions and news on Reddit",
    backstory="""You are an expert at finding AI news on Reddit.
    You search subreddits like r/artificial, r/MachineLearning, r/technology,
    r/ChatGPT, r/singularity for the latest AI news and discussions.""",
    verbose=True,
    allow_code_execution=False,
)

researcher_youtube = Agent(
    role="YouTube AI Content Researcher",
    goal="Find AI videos about news, launches, and tutorials",
    backstory="""You search YouTube for AI-related content including:
    AI news videos, product announcements, tech reviews, and tutorials.
    You find engaging content about the latest AI developments.""",
    verbose=True,
    allow_code_execution=False,
)

researcher_hn = Agent(
    role="Hacker News AI Scout",
    goal="Find trending AI stories on Hacker News",
    backstory="""You are an expert at finding AI stories on Hacker News.
    You look for stories tagged with AI, machine learning, or programming
    that are trending or have high engagement.""",
    verbose=True,
    allow_code_execution=False,
)

processor_deduplicator = Agent(
    role="Deduplicator",
    goal="Remove duplicate news items by comparing URLs and titles",
    backstory="""You are a quality control expert. You remove duplicate 
    news items by checking if URLs or very similar titles already exist.
    You keep only unique items.""",
    verbose=True,
    allow_code_execution=False,
)

processor_relevance = Agent(
    role="Relevance Filter",
    goal="Filter out low-quality or irrelevant content",
    backstory="""You are an editorial expert. You evaluate each news item
    and remove content that is low quality, spam, or not truly about AI.
    You keep only genuinely useful and relevant AI news.""",
    verbose=True,
    allow_code_execution=False,
)

processor_ranker = Agent(
    role="Trending Ranker",
    goal="Rank news by recency, engagement, and relevance",
    backstory="""You are a ranking expert. You score news items based on:
    recency (newer is better), engagement (likes/comments/upvotes),
    and relevance to AI. You prepare them for display.""",
    verbose=True,
    allow_code_execution=False,
)

processor_summarizer = Agent(
    role="Summarizer",
    goal="Create concise summaries for news items",
    backstory="""You are a summarization expert. You create short, informative
    summaries (2-3 sentences) for each news item. You keep only the most
    important information.""",
    verbose=True,
    allow_code_execution=False,
)

processor_categorizer = Agent(
    role="Categorizer",
    goal="Tag news items with appropriate categories",
    backstory="""You are a categorization expert. You tag each news item with one of:
    - Launch (new AI products/tools)
    - News (company updates, industry news)
    - Research (papers, discoveries, breakthroughs)
    - Tutorial (how-tos, guides, courses)""",
    verbose=True,
    allow_code_execution=False,
)


def run_google_research(task_desc):
    task = Task(
        description=f"""Search the web for new AI launches. Use these search terms:
        - "AI tool launched 2025"
        - "new artificial intelligence released"
        - "AI startup funding announced"
        - "just launched AI product"
        - "AI beta launch"
        - "new AI model announced"
        
        Find at least 10 recent AI news items with titles, summaries, and source links.
        Return results in JSON format with: title, summary, source, url""",
        agent=researcher_google,
        expected_output="JSON list of AI news items",
    )
    crew = Crew(agents=[researcher_google], tasks=[task], process=Process.sequence)
    result = crew.kickoff()
    return result


def run_tech_giants_research():
    all_news = []
    blogs = get_tech_giant_blogs()
    for source, url in blogs.items():
        news = fetch_rss_feed(url, source)
        all_news.extend(news)
    return all_news


def run_reddit_research():
    all_news = []
    subreddits = [
        "artificial",
        "MachineLearning",
        "technology",
        "ChatGPT",
        "singularity",
        "LocalLLaMA",
        "artificial Intelligence",
    ]
    for sub in subreddits:
        news = search_reddit(sub, "AI")
        all_news.extend(news)
    return all_news


def run_youtube_research():
    api_key = os.environ.get("YOUTUBE_API_KEY", "")
    return search_youtube(api_key, "AI news today artificial intelligence launch")


def run_hn_research():
    return search_hackernews("AI")


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
    spam_keywords = ["casino", "gambling", "crypto scam", "free money", "click here"]
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
        if "launch" in title or "announce" in title or "release" in title:
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

    print("1. Researching Google AI...")
    try:
        google_news = run_google_research("Find new AI launches")
        if google_news:
            if hasattr(google_news, "raw"):
                try:
                    parsed = json.loads(str(google_news.raw))
                    all_news.extend(parsed)
                except:
                    all_news.append(
                        {"title": str(google_news), "source_type": "google"}
                    )
    except Exception as e:
        print(f"Google research error: {e}")

    print("2. Monitoring Tech Giants...")
    try:
        all_news.extend(run_tech_giants_research())
    except Exception as e:
        print(f"Tech giants error: {e}")

    print("3. Searching Reddit...")
    try:
        all_news.extend(run_reddit_research())
    except Exception as e:
        print(f"Reddit error: {e}")

    print("4. Searching YouTube...")
    try:
        all_news.extend(run_youtube_research())
    except Exception as e:
        print(f"YouTube error: {e}")

    print("5. Searching Hacker News...")
    try:
        all_news.extend(run_hn_research())
    except Exception as e:
        print(f"HN error: {e}")

    print(f"Total raw items: {len(all_news)}")

    print("6. Deduplicating...")
    all_news = deduplicate_news(all_news)
    print(f"After dedup: {len(all_news)}")

    print("7. Filtering relevance...")
    all_news = filter_relevance(all_news)
    print(f"After filter: {len(all_news)}")

    print("8. Ranking...")
    all_news = rank_news(all_news)

    print("9. Storing in database...")
    db.insert_news(all_news)
    db.mark_processed()
    db.set_last_update()
    db.clear_old_news(72)

    print(f"Done! Stored {len(all_news)} news items")
    return all_news


def get_cached_news(limit=50, category=None, source_type=None):
    return db.get_news(limit, category, source_type)


def get_news_status():
    last_update = db.get_last_update()
    conn = sqlite3.connect(db.db_path)
    c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM news_cache WHERE is_processed = TRUE")
    count = c.fetchone()[0]
    conn.close()
    return {"last_update": last_update, "cached_count": count}


if __name__ == "__main__":
    run_full_crew()
