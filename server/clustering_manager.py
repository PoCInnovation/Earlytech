import logging
from typing import Any, List, Tuple
import numpy as np

from sklearn.preprocessing import StandardScaler
from hdbscan import HDBSCAN 

logger = logging.getLogger(__name__)


def run_clustering(db_manager: Any):
    """
    Launches the clustering process on all articles with embeddings.
    
    Args:
        db_manager: The DatabaseManager instance to read embeddings and update clusters.
    """
    logger.info("=" * 60)
    logger.info("🧠 CLUSTERING MODE START (HDBSCAN)")
    logger.info("=" * 60)
    
    try:
        logger.info("1. Retrieving all embeddings from the database...")
        data = db_manager.get_all_embeddings_with_ids()
        
        if not data:
            logger.warning("No embeddings found. Clustering skipped.")
            return

        article_ids: List[str] = [item[0] for item in data]
        # Les embeddings sont des tableaux numpy sérialisés que DatabaseManager doit désérialiser
        embeddings: np.ndarray = np.array([item[1] for item in data])
        
        logger.info(f"  -> {len(embeddings)} embeddings retrieved.")
        
        # 2. Prétraitement (Mise à l'échelle - souvent utile pour le clustering)
        logger.info("2. Preprocessing embeddings (Scaling)...")
        scaler = StandardScaler()
        scaled_embeddings = scaler.fit_transform(embeddings)

        # 3. Application de l'algorithme HDBSCAN
        logger.info("3. Applying HDBSCAN clustering (DBSCAN Hiérarchique)...")
        # min_cluster_size=15 est un bon point de départ, à ajuster selon le volume de données
        clusterer = HDBSCAN(
            min_cluster_size=15, 
            metric='euclidean', 
            min_samples=5, # Moins sensible au bruit
        )
        cluster_labels = clusterer.fit_predict(scaled_embeddings)
        
        n_clusters = len(set(cluster_labels)) - (1 if -1 in cluster_labels else 0)
        n_noise = list(cluster_labels).count(-1)
        
        logger.info(f"  -> Clustering complete. Found {n_clusters} clusters.")
        logger.info(f"  -> {n_noise} articles considered noise (-1).")

        # 4. Mise à jour de la base de données
        logger.info("4. Updating articles with cluster IDs...")
        
        updates: List[Tuple[str, int]] = []
        for article_id, label in zip(article_ids, cluster_labels):
            updates.append((article_id, int(label)))
        
        # Cette méthode doit être ajoutée à DatabaseManager
        db_manager.batch_update_cluster_ids(updates)
        
        logger.info(f"  -> {len(updates)} articles updated successfully.")
        
    except Exception as e:
        logger.error(f"Clustering process failed: {e}")
    finally:
        logger.info("=" * 60)
        logger.info("✓ CLUSTERING MODE COMPLETE")
        logger.info("=" * 60)