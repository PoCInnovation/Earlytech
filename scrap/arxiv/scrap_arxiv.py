import time
import os
import sqlite3
import arxiv

CATEGORY = "cs.LG"  # check in category.md
INTERVAL = 300      # secondes
DB_FILE = os.path.join(os.path.dirname(__file__), "arxiv_papers.db")

conn = sqlite3.connect(DB_FILE)
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS papers (
    id TEXT PRIMARY KEY,
    title TEXT,
    authors TEXT,
    published TEXT,
    summary TEXT,
    link TEXT
)
""")
conn.commit()

def save_paper(paper):
    cursor.execute("""
    INSERT OR IGNORE INTO papers (id, title, authors, published, summary, link)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (
        paper.entry_id,
        paper.title,
        ", ".join([a.name for a in paper.authors]),
        paper.published.isoformat(),
        paper.summary,
        paper.entry_id
    ))
    conn.commit()

cursor.execute("SELECT id FROM papers")
seen_ids = set(row[0] for row in cursor.fetchall())

while True:
    search = arxiv.Search(
        query=f"cat:{CATEGORY}",
        max_results=10,
        sort_by=arxiv.SortCriterion.SubmittedDate,
        sort_order=arxiv.SortOrder.Descending
    )

    for result in search.results():
        if result.entry_id not in seen_ids:
            print("NOUVEAU PAPIER !")
            print("Title:", result.title)
            print("Authors:", ", ".join([author.name for author in result.authors]))
            print("Published:", result.published)
            print("Link:", result.entry_id)
            print("="*80)
            
            save_paper(result)
            seen_ids.add(result.entry_id)

    time.sleep(INTERVAL)
