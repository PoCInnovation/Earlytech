import requests
from bs4 import BeautifulSoup
from typing import Dict, Optional, List
from datetime import datetime
import time


class HTMLScraper:
    """Generic HTML scraper for extracting full article content."""

    def __init__(self, user_agent: Optional[str] = None):
        """Initialize the scraper with optional custom user agent."""
        self.user_agent = user_agent or (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/120.0.0.0 Safari/537.36"
        )
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': self.user_agent})

    def fetch_html(self, url: str, timeout: int = 30) -> Optional[str]:
        """Fetch HTML content from URL."""
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            return response.text
        except Exception as e:
            print(f"❌ Error fetching {url}: {e}")
            return None

    def scrape_medium_article(self, url: str) -> Optional[Dict]:
        """Scrape a Medium article and extract all content."""
        html = self.fetch_html(url)
        if not html:
            return None

        try:
            soup = BeautifulSoup(html, 'html.parser')

            title = self._extract_title(soup)
            author = self._extract_author(soup)
            publish_date = self._extract_publish_date(soup)
            content = self._extract_full_content(soup)
            top_image = self._extract_top_image(soup)
            tags = self._extract_tags(soup)

            return {
                'url': url,
                'title': title,
                'author': author,
                'publish_date': publish_date,
                'content': content,
                'top_image': top_image,
                'tags': tags,
                'scraped_at': datetime.now().isoformat(),
                'word_count': len(content.split()) if content else 0
            }

        except Exception as e:
            print(f"❌ Error parsing {url}: {e}")
            return None

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract article title."""
        selectors = [
            'h1',
            'article h1',
            '[data-testid="storyTitle"]',
            'meta[property="og:title"]',
        ]

        for selector in selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    return element.get('content')
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)

        return "Title not found"

    def _extract_author(self, soup: BeautifulSoup) -> str:
        """Extract article author."""
        selectors = [
            'meta[name="author"]',
            'meta[property="article:author"]',
            'a[rel="author"]',
            '[data-testid="authorName"]',
        ]

        for selector in selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    return element.get('content')
            else:
                element = soup.select_one(selector)
                if element:
                    return element.get_text(strip=True)

        return "Author not found"

    def _extract_publish_date(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract publication date."""
        selectors = [
            'meta[property="article:published_time"]',
            'meta[name="publish_date"]',
            'time[datetime]',
        ]

        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                if selector.startswith('meta'):
                    return element.get('content')
                elif selector == 'time[datetime]':
                    return element.get('datetime')

        return None

    def _extract_full_content(self, soup: BeautifulSoup) -> str:
        """Extract all article content using multiple approaches."""
        content_parts = []

        article = soup.find('article')
        if article:
            paragraphs = article.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote', 'pre'])
            for para in paragraphs:
                text = para.get_text(strip=True)
                if text and len(text) > 10:
                    content_parts.append(text)

        if not content_parts:
            content_divs = soup.find_all(['div', 'section'], class_=lambda x: x and any(
                keyword in str(x).lower() for keyword in ['content', 'article', 'post', 'story']
            ))

            for div in content_divs:
                paragraphs = div.find_all(['p', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'li', 'blockquote'])
                for para in paragraphs:
                    text = para.get_text(strip=True)
                    if text and len(text) > 10:
                        content_parts.append(text)

        if not content_parts:
            all_paragraphs = soup.find_all('p')
            for para in all_paragraphs:
                text = para.get_text(strip=True)
                if text and len(text) > 20:
                    content_parts.append(text)

        cleaned_parts = []
        seen = set()
        for part in content_parts:
            cleaned = ' '.join(part.split())
            if cleaned and cleaned not in seen and len(cleaned) > 20:
                cleaned_parts.append(cleaned)
                seen.add(cleaned)

        full_content = '\n\n'.join(cleaned_parts)
        return full_content if full_content else "Content not found"

    def _extract_top_image(self, soup: BeautifulSoup) -> Optional[str]:
        """Extract main article image."""
        selectors = [
            'meta[property="og:image"]',
            'meta[name="twitter:image"]',
            'article img',
        ]

        for selector in selectors:
            if selector.startswith('meta'):
                element = soup.select_one(selector)
                if element and element.get('content'):
                    return element.get('content')
            else:
                element = soup.select_one(selector)
                if element and element.get('src'):
                    return element.get('src')

        return None

    def _extract_tags(self, soup: BeautifulSoup) -> List[str]:
        """Extract article tags and categories."""
        tags = []

        meta_keywords = soup.select_one('meta[name="keywords"]')
        if meta_keywords and meta_keywords.get('content'):
            tags.extend([tag.strip() for tag in meta_keywords.get('content').split(',')])

        tag_links = soup.find_all('a', href=lambda x: x and '/tag/' in str(x))
        for link in tag_links:
            tag_text = link.get_text(strip=True)
            if tag_text and tag_text not in tags:
                tags.append(tag_text)

        return tags

    def scrape_multiple_articles(self, urls: List[str], delay: int = 2) -> List[Dict]:
        """Scrape multiple articles with delay between requests."""
        articles = []
        total = len(urls)

        for i, url in enumerate(urls, 1):
            print(f"\n[{i}/{total}] Scraping: {url}")

            article = self.scrape_medium_article(url)
            if article:
                articles.append(article)
                print(f"✅ Article scraped: {article['title']}")
                print(f"   Words: {article['word_count']}")

            if i < total:
                time.sleep(delay)

        print(f"\n✨ Total: {len(articles)} articles scraped")
        return articles

    def save_to_file(self, articles: List[Dict], filename: str = "scraped_articles.txt"):
        """Save articles to text file."""
        with open(filename, 'w', encoding='utf-8') as f:
            for article in articles:
                f.write(f"\n{'='*80}\n")
                f.write(f"TITLE: {article['title']}\n")
                f.write(f"AUTHOR: {article['author']}\n")
                f.write(f"DATE: {article['publish_date']}\n")
                f.write(f"URL: {article['url']}\n")
                f.write(f"TAGS: {', '.join(article['tags'])}\n")
                f.write(f"WORD COUNT: {article['word_count']}\n")
                f.write(f"\n{'-'*80}\n")
                f.write(f"CONTENT:\n\n{article['content']}\n")

        print(f"\n💾 Articles saved to {filename}")


if __name__ == "__main__":
    scraper = HTMLScraper()

    test_urls = [
        "https://medium.com/@satvik.jain.kht/bert-and-its-tokenization-explained-intuitively-a986f952c491"
    ]

    articles = scraper.scrape_multiple_articles(test_urls, delay=3)

    if articles:
        scraper.save_to_file(articles, "medium_full_articles.txt")

        if len(articles) > 0:
            print("\n" + "="*60)
            print("FIRST ARTICLE PREVIEW:")
            print("="*60)
            first = articles[0]
            print(f"Title: {first['title']}")
            print(f"Author: {first['author']}")
            print(f"Words: {first['word_count']}")
            print(f"\nContent (excerpt):\n{first['content'][:300]}...")
