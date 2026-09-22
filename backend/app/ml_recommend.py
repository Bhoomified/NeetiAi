"""
Collaborative-filtering-style recommendations: finds peers with similar
spending profiles to the current user, then surfaces what those peers
actually cut and saved by.

NOTE: peer data is synthetic (see notebooks/) — real collaborative filtering
requires real usage data at scale this app doesn't have yet. Architecture is
real and would work identically once seeded with genuine peer data.
"""
import os
import pandas as pd
import numpy as np

CATEGORIES = ["food", "transport", "shopping", "entertainment", "recharge", "education", "rent"]
PEER_DATA_PATH = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "peer_outcomes.csv")

_peers_df = None
if os.path.exists(PEER_DATA_PATH):
    _peers_df = pd.read_csv(PEER_DATA_PATH)
    print(f"✅ Loaded {len(_peers_df)} peer profiles for recommendations")
else:
    print(f"⚠️  No peer data found at {PEER_DATA_PATH} — recommendations unavailable")


def _cosine_similarity(a: np.ndarray, b: np.ndarray) -> float:
    denom = (np.linalg.norm(a) * np.linalg.norm(b))
    if denom == 0:
        return 0.0
    return float(np.dot(a, b) / denom)


def get_peer_recommendation(user_category_spend: dict, top_k: int = 15) -> dict:
    """
    user_category_spend: {"food": 320, "transport": 180, ...} — current user's actual spend.
    Finds the most similar peers, then reports the most common cut + average savings among them.
    """
    if _peers_df is None or len(_peers_df) == 0:
        return {"available": False, "note": "No peer data available yet."}

    user_vec = np.array([user_category_spend.get(c, 0.0) for c in CATEGORIES])
    if user_vec.sum() == 0:
        return {"available": False, "note": "Not enough spending history to compare against peers."}

    peer_vecs = _peers_df[CATEGORIES].values
    similarities = np.array([_cosine_similarity(user_vec, peer_vecs[i]) for i in range(len(peer_vecs))])

    top_indices = similarities.argsort()[::-1][:top_k]
    top_peers = _peers_df.iloc[top_indices]

    if len(top_peers) == 0:
        return {"available": False, "note": "Could not find comparable peers."}

    # Most common category these similar peers actually cut
    most_common_cut = top_peers["cut_category"].mode()
    if len(most_common_cut) == 0:
        return {"available": False, "note": "No clear pattern among peers."}

    top_cut_category = most_common_cut.iloc[0]
    matching = top_peers[top_peers["cut_category"] == top_cut_category]
    avg_cut_pct = round(matching["cut_pct"].mean(), 1)
    peer_count = len(matching)
    similarity_avg = round(float(similarities[top_indices].mean()) * 100, 1)

    return {
        "available": True,
        "category": top_cut_category,
        "avg_cut_pct": avg_cut_pct,
        "peer_count": peer_count,
        "similarity_confidence": similarity_avg,
        "note": "Based on similar spending profiles — currently seeded with synthetic peer data.",
    }