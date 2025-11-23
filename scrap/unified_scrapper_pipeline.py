import sqlite3
# Importation de UTC pour la gestion moderne du temps
from datetime import datetime, UTC 
from typing import List, Dict
import time
import os

# 💡 Assurez-vous d'importer vos fonctions de scraping normalisées
# J'utilise les noms de modules que vous avez fournis
from scrape_hf import scrape_huggingface
from scrape_github import scrape_github
from medium_scraping import scrape_medium
from scrap_arxiv import scrape_arxiv
from scrap_le_monde import scrape_lemonde 


DB_FILE = "veille_technique_unified.db"

def setup_database():
    """Initialise la base de données et crée la table unifiée."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("""
    CREATE TABLE IF NOT EXISTS unified_data (
        id TEXT PRIMARY KEY,
        source_site TEXT NOT NULL,
        title TEXT NOT NULL,
        description TEXT,
        author_info TEXT,
        keywords TEXT,
        content_url TEXT NOT NULL,
        published_date TEXT,
        item_type TEXT,
        created_at TIMESTAMP
    )
    """)
    conn.commit()
    conn.close()

def save_unified_item(item: Dict, conn: sqlite3.Connection):
    """Insère un élément unifié dans la base de données."""
    cur = conn.cursor()
    # ✅ CORRECTION 1: Utilisation de datetime.now(UTC) pour éviter la dépréciation
    now = datetime.now(UTC).isoformat()
    
    # Utilisation d'INSERT OR IGNORE pour gérer le dédoublonnage par l'ID
    cur.execute("""
    INSERT OR IGNORE INTO unified_data 
    (id, source_site, title, description, author_info, keywords, content_url, published_date, item_type, created_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        item["id"],
        item["source_site"],
        item["title"],
        item["description"],
        item["author_info"],
        item["keywords"],
        item["content_url"],
        item["published_date"],
        item["item_type"],
        now
    ))
    conn.commit()

def run_scrapers_and_save():
    """Exécute tous les scrapers, collecte les données et les sauvegarde."""
    print("--- Démarrage du Pipeline de Veille Technique ---")
    setup_database()
    
    conn = sqlite3.connect(DB_FILE)
    
    scrapers = [
        ("Hugging Face", scrape_huggingface, 10),
        ("GitHub", scrape_github, 5),
        ("Medium", scrape_medium, 5),
        ("arXiv", scrape_arxiv, 10),
        ("Le Monde", scrape_lemonde, None),
    ]
    
    total_new_items = 0
    
    for name, scraper_func, limit in scrapers:
        print(f"\n🚀 Lancement du scraper : **{name}**")
        
        try:
            items = scraper_func(limit) if limit is not None else scraper_func() 
            
            # ✅ CORRECTION 2: Gestion robuste des types de retour non-itérables (comme int ou None)
            
            # Si 'items' est None, ou non-itérable (int), nous le traitons.
            if items is None:
                print(f"   ❌ **ALERTE: Le scraper {name} a retourné None. Skipping.**")
                continue
            
            # Tenter de vérifier l'itérabilité pour attraper l'erreur 'int' object is not iterable
            try:
                # Si l'objet n'est pas itérable (ex: int 403), cette ligne lève une TypeError
                iter(items)
                
            except TypeError:
                print(f"   ❌ **ERREUR FATALE (Non-Itérable)**: Le scraper {name} a retourné un type non itérable ({type(items)}). Skipping.")
                continue

            # À ce stade, 'items' est garanti d'être itérable, mais nous vérifions si c'est une liste
            if not isinstance(items, list):
                 print(f"   ⚠️ WARNING: Le scraper {name} a retourné un objet itérable ({type(items)}) mais pas une liste. Conversion en liste.")
                 items = list(items) # Convertir en liste au cas où ce serait un tuple/set
                 
            print(f"   -> {len(items)} éléments récupérés.")
            
            count_saved = 0
            for item in items:
                # La fonction save_unified_item gère le dédoublonnage (INSERT OR IGNORE)
                save_unified_item(item, conn)
                count_saved += 1
            
            print(f"   -> {count_saved} éléments insérés/vérifiés dans la base de données.")
            total_new_items += count_saved
            
        except Exception as e:
            print(f"   ❌ **ERREUR FATALE** lors du scraping {name}: {e}")
            
    conn.close()
    print(f"\n--- Pipeline Terminé. {total_new_items} éléments traités. ---")
    print(f"Base de données unifiée : **{DB_FILE}**")

def check_results():
    """Affiche les 5 premières entrées de la base de données unifiée."""
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    
    cur.execute("SELECT * FROM unified_data LIMIT 5")
    rows = cur.fetchall()
    
    print("\n--- Aperçu des Résultats Unifiés (5 premières lignes) ---")
    if not rows:
        print("La base de données est vide.")
        return

    # Afficher les noms de colonnes
    column_names = [description[0] for description in cur.description]
    print(f"Colonnes: {column_names}")
    print("-" * 120)

    # Afficher les données
    for row in rows:
        print(row)
        
    cur.execute("SELECT COUNT(*) FROM unified_data")
    total_count = cur.fetchone()[0]
    print(f"\nTotal des éléments dans la DB : **{total_count}**")
    
    conn.close()


if __name__ == "__main__":
    run_scrapers_and_save()
    check_results()