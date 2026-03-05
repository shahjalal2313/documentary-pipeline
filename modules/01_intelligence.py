# modules/01_intelligence.py
import json
import time
from loguru import logger
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

COMPETITOR_CHANNELS = [
    "https://www.youtube.com/@MagnatesMedia",
    "https://www.youtube.com/@ColdFusion",
    "https://www.youtube.com/@PolyMatter",
    "https://www.youtube.com/@WendoverProductions"
]

def get_channel_videos(channel_url, max_videos=30):
    """Scrape channel videos with view counts. No API key needed."""
    import subprocess
    result = subprocess.run([
        "yt-dlp",
        "--flat-playlist",
        "--playlist-end", str(max_videos),
        "--print", "%(title)s|||%(view_count)s",
        channel_url
    ], capture_output=True, text=True, timeout=60)

    videos = []
    for line in result.stdout.strip().split("\n"):
        if "|||" in line:
            title, views = line.split("|||", 1)
            try:
                videos.append({"title": title.strip(), "views": int(views.strip())})
            except:
                pass
    return videos

def find_outlier_topics(channels, outlier_threshold=3.0):
    """Find videos performing 3x above their channel average."""
    all_outliers = []
    for channel in channels:
        logger.info(f"Scanning: {channel}")
        try:
            videos = get_channel_videos(channel)
            if not videos:
                continue
            avg = sum(v["views"] for v in videos) / len(videos)
            for v in videos:
                score = v["views"] / avg if avg > 0 else 0
                if score >= outlier_threshold:
                    all_outliers.append({
                        "title": v["title"],
                        "views": v["views"],
                        "outlier_score": round(score, 2),
                        "channel": channel.split("@")[-1]
                    })
            time.sleep(2)  # be polite to YouTube
        except Exception as e:
            logger.warning(f"Failed to scan {channel}: {e}")
    return sorted(all_outliers, key=lambda x: x["outlier_score"], reverse=True)

def rank_topics_with_llm(outliers, count=15):
    """Use GPT-4o-mini to rank topics for your specific channel."""
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    topic_list = "\n".join([
        f"- {o['title']} ({o['outlier_score']}x avg | {o['views']:,} views | from {o['channel']})"
        for o in outliers[:40]
    ])
    response = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{
            "role": "user",
            "content": f"""You are a YouTube strategy expert for a new business documentary channel.

From these proven viral topics, select and rank the best {count} for a NEW channel to cover.
Prioritize: strong emotional hook, clear villain or hero dynamic, broad curiosity appeal, not oversaturated.
Avoid: topics needing complex crowd scenes or too recent to have full story.

Topics found:
{topic_list}

Return ONLY valid JSON:
{{"ranked_topics": [
  {{"rank": 1, "title": "suggested video title", "original_ref": "original title", "why": "one sentence reason", "hook_angle": "the emotional hook to use", "score": 95}}
]}}"""
        }]
    )
    return json.loads(response.choices[0].message.content)

def run_weekly_intelligence(save_path="output/scripts/weekly_topics.json"):
    """Full weekly intelligence run."""
    logger.info("Starting weekly intelligence run...")
    outliers = find_outlier_topics(COMPETITOR_CHANNELS)
    logger.info(f"Found {len(outliers)} outlier videos")
    ranked = rank_topics_with_llm(outliers)
    os.makedirs(os.path.dirname(save_path), exist_ok=True)
    with open(save_path, "w") as f:
        json.dump(ranked, f, indent=2)
    logger.success(f"Saved {len(ranked['ranked_topics'])} ranked topics to {save_path}")
    return ranked

if __name__ == "__main__":
    results = run_weekly_intelligence()
    print("\n=== TOP 5 TOPICS THIS WEEK ===")
    for t in results["ranked_topics"][:5]:
        print(f"#{t['rank']}: {t['title']}")
        print(f"   Hook: {t['hook_angle']}")
        print(f"   Why: {t['why']}\n")
