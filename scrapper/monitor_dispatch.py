#!/usr/bin/env python3
"""
Real-Time Dispatch Monitor

Shows article dispatching in real-time as articles are processed.
Useful for debugging and verifying the system works.
"""

import os
import sys
import time
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager


def monitor_dispatches(interval_seconds: int = 5):
    """
    Monitor article deliveries in real-time.
    
    Args:
        interval_seconds: How often to check for new deliveries
    """
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    try:
        db = DatabaseManager(db_url)
    except Exception as e:
        print(f" Cannot connect to database: {e}")
        return
    
    print("\n" + "="*80)
    print(" REAL-TIME DISPATCH MONITOR")
    print("="*80)
    print(f"\nMonitoring deliveries every {interval_seconds} seconds...")
    print("Press Ctrl+C to stop\n")
    
    last_delivery_id = 0
    
    # Get initial state
    with db.get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COALESCE(MAX(id), 0) as max_id FROM user_article_delivery")
        last_delivery_id = cur.fetchone()["max_id"]
    
    print(f"Starting from delivery ID: {last_delivery_id}")
    print("-"*80)
    
    try:
        while True:
            with db.get_connection() as conn:
                cur = conn.cursor()
                
                cur.execute("""
                    SELECT 
                        uad.id,
                        u.username,
                        a.title,
                        a.source_site,
                        uk.keyword,
                        uad.similarity_score,
                        uad.delivered_at
                    FROM user_article_delivery uad
                    JOIN users u ON uad.user_id = u.id
                    JOIN articles a ON uad.article_id = a.id
                    JOIN user_keywords uk ON uad.keyword_id = uk.id
                    WHERE uad.id > %s
                    ORDER BY uad.id ASC
                """, (last_delivery_id,))
                
                new_deliveries = cur.fetchall()
                
                if new_deliveries:
                    for delivery in new_deliveries:
                        timestamp = delivery["delivered_at"].strftime("%H:%M:%S")
                        score_pct = delivery["similarity_score"] * 100
                        
                        print(f"\n[{timestamp}]  NEW DELIVERY")
                        print(f"   User: {delivery['username']}")
                        print(f"   Article: {delivery['title'][:60]}...")
                        print(f"   Source: {delivery['source_site']}")
                        print(f"   Matched keyword: '{delivery['keyword']}'")
                        print(f"   Similarity: {score_pct:.1f}%")
                        print("-"*80)
                        
                        last_delivery_id = delivery["id"]
                
                # Show stats
                cur.execute("""
                    SELECT 
                        COUNT(DISTINCT user_id) as users,
                        COUNT(DISTINCT article_id) as articles,
                        COUNT(*) as deliveries,
                        AVG(similarity_score) as avg_score
                    FROM user_article_delivery
                    WHERE delivered_at > NOW() - INTERVAL '1 hour'
                """)
                
                stats = cur.fetchone()
                
                # Clear line and show stats (no newline spam)
                sys.stdout.write(f"\rLast hour: {stats['deliveries']} deliveries to {stats['users']} users | Avg score: {(stats['avg_score'] or 0)*100:.1f}%")
                sys.stdout.flush()
            
            time.sleep(interval_seconds)
            
    except KeyboardInterrupt:
        print("\n\n  Monitor stopped")
    except Exception as e:
        print(f"\n\n Error: {e}")
        import traceback
        traceback.print_exc()


def show_recent_dispatches(limit: int = 10):
    """Show most recent article dispatches."""
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    try:
        db = DatabaseManager(db_url)
    except Exception as e:
        print(f" Cannot connect to database: {e}")
        return
    
    print("\n" + "="*80)
    print(f"RECENT DISPATCHES (Last {limit})")
    print("="*80)
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        cur.execute("""
            SELECT 
                u.username,
                a.title,
                a.source_site,
                uk.keyword,
                uad.similarity_score,
                uad.delivered_at
            FROM user_article_delivery uad
            JOIN users u ON uad.user_id = u.id
            JOIN articles a ON uad.article_id = a.id
            JOIN user_keywords uk ON uad.keyword_id = uk.id
            ORDER BY uad.delivered_at DESC
            LIMIT %s
        """, (limit,))
        
        deliveries = cur.fetchall()
        
        if not deliveries:
            print("\nNo deliveries found")
            return
        
        for i, d in enumerate(deliveries, 1):
            timestamp = d["delivered_at"].strftime("%Y-%m-%d %H:%M:%S")
            score_pct = d["similarity_score"] * 100
            
            print(f"\n{i}. [{timestamp}]")
            print(f"User: {d['username']}")
            print(f"Article: {d['title'][:60]}...")
            print(f"Source: {d['source_site']}")
            print(f"    Keyword: '{d['keyword']}' ({score_pct:.1f}% match)")
    
    print("\n" + "="*80)


def show_dispatch_stats():
    """Show overall dispatch statistics."""
    
    db_url = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/veille_technique")
    
    try:
        db = DatabaseManager(db_url)
    except Exception as e:
        print(f" Cannot connect to database: {e}")
        return
    
    print("\n" + "="*80)
    print(" DISPATCH STATISTICS")
    print("="*80)
    
    with db.get_connection() as conn:
        cur = conn.cursor()
        
        # Overall stats
        cur.execute("""
            SELECT 
                COUNT(DISTINCT user_id) as total_users,
                COUNT(DISTINCT article_id) as total_articles,
                COUNT(*) as total_deliveries,
                AVG(similarity_score) as avg_similarity,
                MIN(similarity_score) as min_similarity,
                MAX(similarity_score) as max_similarity
            FROM user_article_delivery
        """)
        
        stats = cur.fetchone()
        
        print(f"\n Overall:")
        print(f"   • Total users receiving articles: {stats['total_users']}")
        print(f"   • Total articles dispatched: {stats['total_articles']}")
        print(f"   • Total deliveries: {stats['total_deliveries']}")
        print(f"   • Average similarity: {(stats['avg_similarity'] or 0)*100:.1f}%")
        print(f"   • Min similarity: {(stats['min_similarity'] or 0)*100:.1f}%")
        print(f"   • Max similarity: {(stats['max_similarity'] or 0)*100:.1f}%")
        
        # Top users
        cur.execute("""
            SELECT 
                u.username,
                COUNT(*) as article_count,
                AVG(uad.similarity_score) as avg_score
            FROM user_article_delivery uad
            JOIN users u ON uad.user_id = u.id
            GROUP BY u.id, u.username
            ORDER BY article_count DESC
            LIMIT 5
        """)
        
        top_users = cur.fetchall()
        
        print(f"\n👥 Top Users (by articles received):")
        for i, user in enumerate(top_users, 1):
            print(f"   {i}. {user['username']}: {user['article_count']} articles (avg: {user['avg_score']*100:.1f}%)")
        
        # Top keywords
        cur.execute("""
            SELECT 
                uk.keyword,
                COUNT(*) as match_count,
                AVG(uad.similarity_score) as avg_score
            FROM user_article_delivery uad
            JOIN user_keywords uk ON uad.keyword_id = uk.id
            GROUP BY uk.keyword
            ORDER BY match_count DESC
            LIMIT 5
        """)
        
        top_keywords = cur.fetchall()
        
        print(f"\n Top Keywords (by matches):")
        for i, kw in enumerate(top_keywords, 1):
            print(f"   {i}. '{kw['keyword']}': {kw['match_count']} matches (avg: {kw['avg_score']*100:.1f}%)")
        
        # Recent activity
        cur.execute("""
            SELECT 
                DATE_TRUNC('hour', delivered_at) as hour,
                COUNT(*) as deliveries
            FROM user_article_delivery
            WHERE delivered_at > NOW() - INTERVAL '24 hours'
            GROUP BY hour
            ORDER BY hour DESC
            LIMIT 10
        """)
        
        activity = cur.fetchall()
        
        if activity:
            print(f"\n⏰ Activity (last 24 hours):")
            for row in activity:
                hour_str = row['hour'].strftime("%Y-%m-%d %H:00")
                print(f"   {hour_str}: {row['deliveries']} deliveries")
    
    print("\n" + "="*80)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor article dispatches")
    parser.add_argument("command", nargs="?", choices=["monitor", "recent", "stats"], 
                       default="recent", help="Command to run")
    parser.add_argument("--interval", type=int, default=5, 
                       help="Monitoring interval in seconds (for monitor command)")
    parser.add_argument("--limit", type=int, default=10,
                       help="Number of recent dispatches to show (for recent command)")
    
    args = parser.parse_args()
    
    try:
        if args.command == "monitor":
            monitor_dispatches(args.interval)
        elif args.command == "recent":
            show_recent_dispatches(args.limit)
        elif args.command == "stats":
            show_dispatch_stats()
    except Exception as e:
        print(f"\n Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
