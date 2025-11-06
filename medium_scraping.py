import feedparser
from html_scrapper import HTMLScraper
from typing import List, Dict, Optional
import time


class MediumScraper:
    """Scraper for Medium AI articles."""

    RSS_FEEDS = [
        "https://medium.com/feed/tag/artificial-intelligence",
        "https://medium.com/feed/tag/machine-learning",
        "https://medium.com/feed/tag/deep-learning",
        "https://medium.com/feed/tag/ai",
    ]

    def __init__(self):
        self.articles_data = []
        self.html_scraper = HTMLScraper()

    def fetch_rss_feeds(self, max_articles_per_feed: int = 10) -> List[Dict]:
        """Fetch articles from Medium RSS feeds."""
        all_entries = []

        for feed_url in self.RSS_FEEDS:
            print(f"📡 Fetching RSS: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:max_articles_per_feed]:
                    article_info = {
                        'title': entry.get('title', 'N/A'),
                        'link': entry.get('link', ''),
                        'published': entry.get('published', 'N/A'),
                        'summary': entry.get('summary', 'N/A'),
                        'author': entry.get('author', 'N/A'),
                        'tags': [tag.term for tag in entry.get('tags', [])] if 'tags' in entry else []
                    }
                    all_entries.append(article_info)
                print(f"✅ {len(feed.entries[:max_articles_per_feed])} articles fetched")
            except Exception as e:
                print(f"❌ Error fetching {feed_url}: {e}")
            time.sleep(1)

        print(f"\n📊 Total: {len(all_entries)} articles from all feeds")
        return all_entries

    def scrape_article_content(self, url: str) -> Optional[Dict]:
        """Scrape full HTML content of a Medium article."""
        return self.html_scraper.scrape_medium_article(url)

    def scrape_articles_from_rss(self, max_articles: int = 20, delay: int = 2) -> List[Dict]:
        """Fetch RSS feeds and scrape full content of each article."""
        print("=" * 60)
        print("STEP 1: Fetching RSS feeds")
        print("=" * 60)
        rss_entries = self.fetch_rss_feeds(max_articles_per_feed=max_articles)

        unique_urls = list({entry['link'] for entry in rss_entries})[:max_articles]

        print("\n" + "=" * 60)
        print(f"STEP 2: Scraping {len(unique_urls)} articles")
        print("=" * 60)

        scraped_articles = []
        for i, url in enumerate(unique_urls, 1):
            print(f"\n[{i}/{len(unique_urls)}] Scraping: {url}")
            content = self.scrape_article_content(url)
            if content:
                scraped_articles.append(content)
                print(f"✅ Article scraped: {content['title']}")
            if i < len(unique_urls):
                time.sleep(delay)

        self.articles_data = scraped_articles

        print("\n" + "=" * 60)
        print(f"✨ Scraping done: {len(scraped_articles)} articles")
        print("=" * 60)

        return scraped_articles

    def save_to_file(self, filename: str = "medium_articles.txt"):
        """Save articles to text file."""
        with open(filename, 'w', encoding='utf-8') as f:
            for article in self.articles_data:
                f.write(f"\n{'='*80}\n")
                f.write(f"TITLE: {article['title']}\n")
                f.write(f"AUTHOR: {article['author']}\n")
                f.write(f"DATE: {article['publish_date']}\n")
                f.write(f"URL: {article['url']}\n")
                f.write(f"TAGS: {', '.join(article['tags'])}\n")
                f.write(f"WORD COUNT: {article['word_count']}\n")
                f.write(f"\n{article['content']}\n")

        print(f"💾 Articles saved to {filename}")


if __name__ == "__main__":
    scraper = MediumScraper()
    articles = scraper.scrape_articles_from_rss(max_articles=2, delay=5)

    if articles:
        scraper.save_to_file("medium_ai_articles.txt")

        if len(articles) > 0:
            print("\n" + "="*60)
            print("FIRST ARTICLE PREVIEW:")
            print("="*60)
            first = articles[0]
            print(f"Title: {first['title']}")
            print(f"Author: {first['author']}")
            print(f"Date: {first['publish_date']}")
            print(f"Words: {first['word_count']}")
            print(f"Content (excerpt): {first['content'][:300]}...")
