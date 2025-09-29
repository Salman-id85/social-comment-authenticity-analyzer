
import os
import re
import sys
import argparse
import requests
from urllib.parse import urlparse, parse_qs
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from langdetect import detect, LangDetectException
import matplotlib.pyplot as plt
from io import BytesIO

# ----------------- Utilities -----------------

def detect_platform_from_url(url: str) -> str:
    """Detect the social media platform from a URL."""
    url = url.lower()
    if 'youtube.com' in url or 'youtu.be' in url:
        return 'youtube'
    if 'instagram.com' in url:
        return 'instagram'
    if 'facebook.com' in url:
        return 'facebook'
    if 'x.com' in url or 'twitter.com' in url:
        return 'x'
    if 'linkedin.com' in url:
        return 'linkedin'
    return 'unknown'

def extract_youtube_id(url: str) -> str:
    """Extract YouTube video ID from a URL."""
    try:
        p = urlparse(url)
        if 'youtu.be' in p.netloc:
            return p.path.lstrip('/')
        qs = parse_qs(p.query)
        return qs.get('v', [None])[0]
    except Exception:
        return None

# ----------------- Fetchers -----------------

def fetch_youtube_comments(video_id: str, api_key: str, max_results: int = 100) -> list:
    """Fetch comments from a YouTube video using the API."""
    if not api_key:
        print("⚠️ [YouTube] No API key provided. Try setting YOUTUBE_API_KEY.")
        return []
    comments = []
    url = "https://www.googleapis.com/youtube/v3/commentThreads"
    params = {
        "part": "snippet",
        "videoId": video_id,
        "textFormat": "plainText",
        "maxResults": min(max_results, 100),
        "key": api_key,
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        for item in data.get("items", []):
            s = item["snippet"]["topLevelComment"]["snippet"]
            comments.append({
                "author": s.get("authorDisplayName", "Unknown"),
                "text": s.get("textDisplay", ""),
                "publishedAt": s.get("publishedAt", ""),
                "likeCount": s.get("likeCount", 0),
                "platform": "youtube",
            })
    except Exception as e:
        print(f"❌ [YouTube] Error fetching comments: {e}")
    return comments

def fetch_facebook_comments(object_id: str, access_token: str, max_results: int = 100) -> list:
    """Fetch comments from a Facebook post using the Graph API."""
    if not access_token:
        print("⚠️ [Facebook] No access token provided. Try setting FACEBOOK_ACCESS_TOKEN.")
        return []
    comments = []
    url = f"https://graph.facebook.com/v15.0/{object_id}/comments"
    params = {
        "access_token": access_token,
        "limit": min(max_results, 100),
        "filter": "stream",
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        for item in data.get("data", []):
            comments.append({
                "author": item.get("from", {}).get("name", "Unknown"),
                "text": item.get("message", ""),
                "publishedAt": item.get("created_time", ""),
                "likeCount": item.get("like_count", 0),
                "platform": "facebook",
            })
    except Exception as e:
        print(f"❌ [Facebook] Error fetching comments: {e}")
    return comments

def fetch_instagram_comments(media_id: str, access_token: str, max_results: int = 100) -> list:
    """Fetch comments from an Instagram post using the Graph API."""
    if not access_token:
        print("⚠️ [Instagram] No access token provided. Try setting FACEBOOK_ACCESS_TOKEN.")
        return []
    comments = []
    url = f"https://graph.facebook.com/v15.0/{media_id}/comments"
    params = {
        "access_token": access_token,
        "limit": min(max_results, 100),
    }
    try:
        r = requests.get(url, params=params, timeout=15)
        r.raise_for_status()
        data = r.json()
        for item in data.get("data", []):
            comments.append({
                "author": item.get("username", item.get("from", {}).get("name", "Unknown")),
                "text": item.get("text", item.get("message", "")),
                "publishedAt": item.get("timestamp", ""),
                "likeCount": item.get("like_count", 0),
                "platform": "instagram",
            })
    except Exception as e:
        print(f"❌ [Instagram] Error fetching comments: {e}")
    return comments

def fetch_x_comments(tweet_id: str, bearer_token: str, max_results: int = 100) -> list:
    """Placeholder for fetching X/Twitter comments (requires elevated API access)."""
    if not bearer_token:
        print("⚠️ [X/Twitter] No bearer token provided. Try setting TWITTER_BEARER_TOKEN.")
        return []
    print("ℹ️ [X/Twitter] Fetching replies requires Twitter API v2 elevated access. Using demo mode.")
    return []

def fetch_linkedin_comments(urn: str, access_token: str, max_results: int = 100) -> list:
    """Placeholder for fetching LinkedIn comments (requires specific API permissions)."""
    print("ℹ️ [LinkedIn] LinkedIn API fetching not implemented (requires app + permissions). Using demo mode.")
    return []

# ----------------- Sample Demo Comments -----------------

def load_sample_comments(platform: str) -> list:
    """Load hardcoded sample comments for demo purposes if API fetch fails."""
    samples = {
        'youtube': [
            {'author': 'User123', 'text': 'Great video! Loved it.', 'publishedAt': '2023-01-01', 'likeCount': 10, 'platform': 'youtube'},
            {'author': 'BotLike456', 'text': 'Check my channel for free stuff! https://example.com', 'publishedAt': '2023-01-02', 'likeCount': 0, 'platform': 'youtube'},
            {'author': 'RealFan', 'text': 'This changed my perspective.', 'publishedAt': '2023-01-03', 'likeCount': 5, 'platform': 'youtube'},
            {'author': 'SpamBot789', 'text': 'Call now 1234567890 for deals!!!', 'publishedAt': '2023-01-04', 'likeCount': 0, 'platform': 'youtube'},
        ],
        'facebook': [
            {'author': 'FriendA', 'text': 'Nice post!', 'publishedAt': '2023-02-01', 'likeCount': 15, 'platform': 'facebook'},
            {'author': 'PromoBot', 'text': 'Follow me for more', 'publishedAt': '2023-02-02', 'likeCount': 1, 'platform': 'facebook'},
        ],
        'instagram': [
            {'author': 'Follower1', 'text': '🔥🔥🔥', 'publishedAt': '2023-03-01', 'likeCount': 20, 'platform': 'instagram'},
            {'author': 'FakeUser', 'text': 'DM for collab', 'publishedAt': '2023-03-02', 'likeCount': 0, 'platform': 'instagram'},
        ],
        'x': [
            {'author': 'TweeterX', 'text': 'Interesting thread.', 'publishedAt': '2023-04-01', 'likeCount': 8, 'platform': 'x'},
            {'author': 'BotTweet', 'text': 'Visit my site: http://spam.com', 'publishedAt': '2023-04-02', 'likeCount': 0, 'platform': 'x'},
        ],
        'linkedin': [
            {'author': 'Professional1', 'text': 'Valuable insights.', 'publishedAt': '2023-05-01', 'likeCount': 12, 'platform': 'linkedin'},
            {'author': 'NetworkBot', 'text': 'Connect with me for opportunities.', 'publishedAt': '2023-05-02', 'likeCount': 2, 'platform': 'linkedin'},
        ],
        'unknown': [
            {'author': 'DefaultUser', 'text': 'Sample comment.', 'publishedAt': '2023-06-01', 'likeCount': 3, 'platform': 'unknown'},
        ]
    }
    print(f"ℹ️ [Demo Mode] Loading sample comments for {platform} since API fetch failed or keys are missing.")
    return samples.get(platform, samples['unknown'])

# ----------------- CSV Reader -----------------

def read_comments_csv(path: str) -> list:
    """Read comments from a CSV file with columns: author,text,publishedAt,likeCount,platform."""
    import csv
    comments = []
    try:
        with open(path, newline='', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            if reader.fieldnames is None:
                f.seek(0)
                for ln in f:
                    parts = ln.strip().split(',')
                    if len(parts) < 2:
                        continue
                    comments.append({
                        'author': parts[0].strip(),
                        'text': parts[1].strip(),
                        'publishedAt': parts[2].strip() if len(parts) > 2 else '',
                        'likeCount': int(parts[3]) if len(parts) > 3 and parts[3].isdigit() else 0,
                        'platform': parts[4].strip() if len(parts) > 4 else 'unknown'
                    })
            else:
                for row in reader:
                    comments.append({
                        'author': row.get('author') or row.get('user') or row.get('username') or 'Unknown',
                        'text': row.get('text') or row.get('comment') or '',
                        'publishedAt': row.get('publishedAt') or row.get('time') or '',
                        'likeCount': int(row.get('likeCount') or row.get('likes') or 0),
                        'platform': row.get('platform') or 'unknown'
                    })
        print(f"✅ [CSV] Successfully loaded {len(comments)} comments from {path}")
    except Exception as e:
        print(f"❌ [CSV] Error reading file: {e}")
    return comments

# ----------------- Analyzer -----------------

def detect_language(text: str) -> str:
    """Detect the language of a text string."""
    try:
        return detect(text)
    except LangDetectException:
        return 'unknown'

def analyze_comment(comment: dict) -> dict:
    """Analyze a comment for authenticity using heuristics."""
    text = (comment.get('text') or '').strip()
    author = (comment.get('author') or '').strip()
    like = int(comment.get('likeCount') or 0)
    platform = comment.get('platform') or 'unknown'

    score = 60  # Start slightly optimistic
    reasons = []

    # Suspicious tokens: links, phone numbers
    if re.search(r'https?://|www\.', text):
        score -= 35
        reasons.append('Contains a URL or web link (common in spam).')
    if re.search(r'\b\d{7,}\b', text):
        score -= 10
        reasons.append('Contains a long numeric sequence (could be phone/ID).')
    if re.search(r'([!?.]){3,}', text) or re.search(r'(.)\1{6,}', text):
        score -= 8
        reasons.append('Excessive punctuation or repeated characters.')
    emoji_count = len(re.findall(r'[\U0001F300-\U0001F6FF\U0001F900-\U0001F9FF\u2600-\u27BF]', text))
    if emoji_count >= 4:
        score -= 6
        reasons.append('High emoji density (can indicate low-effort engagement).')
    if len(text) <= 4 or text.lower() in ('nice', 'good', 'great', '👍', '🔥'):
        score -= 12
        reasons.append('Very short or generic praise; often low-effort or bot-like.')
    if re.search(r'follow me|check my profile|subscribe|dm for|contact me|visit my', text, flags=re.I):
        score -= 30
        reasons.append('Self-promotional call-to-action (common spam).')
    if like == 0:
        score -= 4
    elif like >= 25:
        score += 10
        reasons.append('High likes — social traction suggests authenticity.')
    if author:
        digits = sum(ch.isdigit() for ch in author)
        if digits >= 3 or re.search(r'user\d{2,}', author, flags=re.I):
            score -= 10
            reasons.append('Author name contains many digits / generic pattern (possible bot).')
        if len(author) <= 2 and author.isalpha():
            score -= 6
            reasons.append('Suspiciously short username (could be fake).')
        if re.search(r'(bot|spam|free|promo)', author, flags=re.I):
            score -= 20
            reasons.append('Username contains bot/promo keywords.')
    lang = detect_language(text) if text else 'unknown'
    if lang == 'unknown':
        reasons.append('Language could not be reliably detected.')
    else:
        if platform in ('facebook', 'instagram') and lang not in ('en', 'unknown'):
            if len(text) < 20:
                score -= 6
                reasons.append('Short comment in an unexpected language for this post (weak signal).')

    score = max(0, min(100, score))
    if score >= 60:
        verdict = 'real'
    elif score >= 40:
        verdict = 'likely-real'
    elif score >= 20:
        verdict = 'likely-fake'
    else:
        verdict = 'fake'

    return {
        'author': author or 'Unknown',
        'text': text,
        'platform': platform,
        'publishedAt': comment.get('publishedAt', ''),
        'likeCount': like,
        'score': score,
        'verdict': verdict,
        'reasons': reasons,
        'language': lang
    }

# ----------------- Visualization -----------------

def create_pie_chart(counts: dict) -> BytesIO:
    """Create a pie chart showing comment authenticity breakdown."""
    labels = [f"{k} ({v})" for k, v in counts.items() if v > 0]
    sizes = [v for v in counts.values() if v > 0]
    if not sizes:
        labels = ['No comments']
        sizes = [1]

    fig, ax = plt.subplots(figsize=(4, 4))
    ax.pie(sizes, labels=labels, autopct='%1.1f%%', colors=['#4CAF50', '#FFC107', '#FF5722', '#D81B60'])
    ax.set_title('Comment Authenticity Breakdown')
    buf = BytesIO()
    plt.tight_layout()
    fig.savefig(buf, format='png', dpi=150)
    plt.close(fig)
    buf.seek(0)
    return buf

# ----------------- PDF Report Generation -----------------

def generate_pdf_report(source: str, platform: str, analysis_list: list, output_path: str) -> None:
    """Generate a PDF report with comment analysis and a pie chart."""
    counts = {}
    for a in analysis_list:
        counts[a['verdict']] = counts.get(a['verdict'], 0) + 1

    pie_buf = create_pie_chart(counts)
    c = canvas.Canvas(output_path, pagesize=A4)
    width, height = A4
    x_margin = 20 * mm
    y = height - 20 * mm

    c.setFont('Helvetica-Bold', 16)
    c.drawString(x_margin, y, "Social Media Comment Veracity Report")
    y -= 8 * mm
    c.setFont('Helvetica', 9)
    c.drawString(x_margin, y, f'Generated: {datetime.utcnow().isoformat()} UTC')
    y -= 6 * mm
    c.drawString(x_margin, y, f'Source: {source}')
    y -= 6 * mm
    c.drawString(x_margin, y, f'Platform: {platform}')
    y -= 10 * mm

    img = ImageReader(pie_buf)
    img_w = 80 * mm
    img_h = 80 * mm
    c.drawImage(img, x_margin, y - img_h, width=img_w, height=img_h)
    y -= img_h + 6 * mm

    total = len(analysis_list)
    real_count = sum(1 for a in analysis_list if a['verdict'] in ('real', 'likely-real'))
    fake_count = total - real_count
    c.setFont('Helvetica-Bold', 11)
    c.drawString(x_margin, y, f"Summary: Total comments: {total} — Likely Real: {real_count} — Likely Fake: {fake_count}")
    y -= 8 * mm

    c.setFont('Helvetica-Bold', 10)
    for i, a in enumerate(analysis_list, start=1):
        if y < 40 * mm:
            c.showPage()
            y = height - 20 * mm
            c.setFont('Helvetica-Bold', 12)
        title = f"{i}. [{a['platform']}] {a['author']} — {a['verdict'].upper()} (score {a['score']})"
        c.drawString(x_margin, y, title)
        y -= 5 * mm
        c.setFont('Helvetica', 9)
        text = a['text'] or ''
        wrap_width = int((width - 2 * x_margin) / 6.5)
        for start in range(0, len(text), wrap_width):
            c.drawString(x_margin + 6 * mm, y, text[start:start+wrap_width])
            y -= 4.5 * mm
        if a['reasons']:
            c.setFont('Helvetica-Oblique', 8)
            for r in a['reasons']:
                for start in range(0, len(r), 110):
                    c.drawString(x_margin + 8 * mm, y, "- " + r[start:start+110])
                    y -= 4 * mm
            y -= 2 * mm
        else:
            c.setFont('Helvetica-Oblique', 8)
            c.drawString(x_margin + 6 * mm, y, "Why: No specific flags detected (manual review recommended).")
            y -= 6 * mm
        y -= 4 * mm
        c.setFont('Helvetica', 9)

    c.save()
    print(f"✅ [Report] Saved to {output_path}")

# ----------------- Orchestration -----------------

def process_url(url: str, args: argparse.Namespace) -> tuple:
    """Process a URL to fetch comments or load demo comments if needed."""
    platform = detect_platform_from_url(url)
    collected = []

    yt_key = os.getenv('YOUTUBE_API_KEY')
    fb_token = os.getenv('FACEBOOK_ACCESS_TOKEN')
    tw_bearer = os.getenv('TWITTER_BEARER_TOKEN') or os.getenv('TWITTER_BEARER') or os.getenv('TWITTER_TOKEN')
    ln_token = os.getenv('LINKEDIN_ACCESS_TOKEN')

    if platform == 'youtube':
        vid = extract_youtube_id(url)
        if vid and yt_key:
            print("ℹ️ [YouTube] Fetching comments via API...")
            collected = fetch_youtube_comments(vid, yt_key, max_results=args.max)
        else:
            print("⚠️ [YouTube] Invalid video ID or missing API key.")
    elif platform == 'facebook':
        if fb_token:
            object_id = url.split('/')[-1] if '/' in url else None
            if object_id:
                print("ℹ️ [Facebook] Fetching comments via API...")
                collected = fetch_facebook_comments(object_id, fb_token, max_results=args.max)
            else:
                print("⚠️ [Facebook] Could not extract post ID from URL.")
        else:
            print("⚠️ [Facebook] Missing access token.")
    elif platform == 'instagram':
        if fb_token:
            media_id = url.split('/')[-2] if '/p/' in url else None
            if media_id:
                print("ℹ️ [Instagram] Fetching comments via API...")
                collected = fetch_instagram_comments(media_id, fb_token, max_results=args.max)
            else:
                print("⚠️ [Instagram] Could not extract media ID from URL.")
        else:
            print("⚠️ [Instagram] Missing access token.")
    elif platform == 'x':
        if tw_bearer:
            tweet_id = url.split('/status/')[-1] if '/status/' in url else None
            if tweet_id:
                print("ℹ️ [X/Twitter] Fetching comments via API...")
                collected = fetch_x_comments(tweet_id, tw_bearer, max_results=args.max)
            else:
                print("⚠️ [X/Twitter] Could not extract tweet ID from URL.")
        else:
            print("⚠️ [X/Twitter] Missing bearer token.")
    elif platform == 'linkedin':
        if ln_token:
            urn = url.split('/')[-1] if '/' in url else None
            if urn:
                print("ℹ️ [LinkedIn] Fetching comments via API...")
                collected = fetch_linkedin_comments(urn, ln_token, max_results=args.max)
            else:
                print("⚠️ [LinkedIn] Could not extract URN from URL.")
        else:
            print("⚠️ [LinkedIn] Missing access token.")
    else:
        print("❌ [Error] Unknown platform.")

    if not collected:
        collected = load_sample_comments(platform)

    return platform, collected

# ----------------- CLI -----------------

def main():
    """Main function with a human-friendly interactive CLI."""
    print("\n🌟 Social Media Comment Analyzer 🌟")
    print("Analyze comments from social media platforms or a CSV file.")
    print("Supported platforms: YouTube, Facebook, Instagram, X/Twitter, LinkedIn")
    print("\nChoose an option:")
    print("  1. Analyze comments from a CSV file")
    print("  2. Analyze comments from a YouTube URL")
    print("  3. Analyze comments from a Facebook URL")
    print("  4. Analyze comments from an Instagram URL")
    print("  5. Analyze comments from an X/Twitter URL")
    print("  6. Analyze comments from a LinkedIn URL")
    
    while True:
        choice = input("\nEnter your choice (1-6): ").strip()
        if choice in {'1', '2', '3', '4', '5', '6'}:
            break
        print("❌ Invalid choice. Please enter a number between 1 and 6.")

    collected = []
    platform = 'unknown'
    source = ""
    args = argparse.Namespace(max=200)

    if choice == "1":
        source = input("📄 Enter the path to your CSV file: ").strip()
        collected = read_comments_csv(source)
        if collected and collected[0].get('platform'):
            platform = collected[0].get('platform')
    elif choice == "2":
        source = input("📺 Enter YouTube video URL: ").strip()
        platform, collected = process_url(source, args)
    elif choice == "3":
        source = input("📘 Enter Facebook post URL: ").strip()
        platform, collected = process_url(source, args)
    elif choice == "4":
        source = input("📸 Enter Instagram post URL: ").strip()
        platform, collected = process_url(source, args)
    elif choice == "5":
        source = input("🐦 Enter X/Twitter post URL: ").strip()
        platform, collected = process_url(source, args)
    elif choice == "6":
        source = input("💼 Enter LinkedIn post URL: ").strip()
        platform, collected = process_url(source, args)

    if not collected:
        print("❌ No comments collected. Please check your input or API keys and try again.")
        sys.exit(1)

    print(f"\nℹ️ Collected {len(collected)} comments. Analyzing...")
    analysis = [analyze_comment(c) for c in collected]
    analysis_sorted = sorted(analysis, key=lambda x: x['score'])

    out_file = "comment_report.pdf"
    print("📝 Generating PDF report...")
    generate_pdf_report(source, platform, analysis_sorted, out_file)
    print(f"🎉 Analysis complete! Report saved to {out_file}")
    print(f"📂 Open {out_file} to view the results.")

if __name__ == "__main__":
    main()
