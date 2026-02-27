"""
Embedding Engine for BrainForce Apollo
Supports both local and API-based embeddings.
"""

import os
import numpy as np
from typing import List, Optional

# Lazy imports
LOCAL_MODEL = None
use_local = False

def init_model():
    """Initialise local embedding model if available."""
    global LOCAL_MODEL, use_local
    try:
        from sentence_transformers import SentenceTransformer
        LOCAL_MODEL = SentenceTransformer("all-MiniLM-L6-v2")
        use_local = True
        print("[EmbeddingEngine] Using local model: all-MiniLM-L6-v2")
    except Exception:
        print("[EmbeddingEngine] Local model not found. Will use API if available.")
        use_local = False

def embed_text(texts: List[str]) -> List[List[float]]:
    """
    Create embeddings for given text list.
    Fallback order:
        1. Local model (if available)
        2. OpenAI API (if OPENAI_API_KEY is set)
        3. Ollama API (if OLLAMA_HOST is set)
        4. Simple numeric hash fallback
    """
    if not texts:
        return []

    if use_local and LOCAL_MODEL:
        return LOCAL_MODEL.encode(texts, convert_to_numpy=True).tolist()

    # API fallback (OpenAI)
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=api_key)
            response = client.embeddings.create(
                model="text-embedding-3-small", input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            print("[EmbeddingEngine] OpenAI embedding failed:", e)

    # Ollama fallback
    ollama_host = os.getenv("OLLAMA_HOST")
    if ollama_host:
        try:
            import requests
            results = []
            for t in texts:
                resp = requests.post(
                    f"{ollama_host}/api/embeddings",
                    json={"model": "nomic-embed-text", "prompt": t},
                    timeout=10,
                )
                results.append(resp.json().get("embedding", []))
            return results
        except Exception as e:
            print("[EmbeddingEngine] Ollama embedding failed:", e)

    # Final fallback: simple deterministic hash vector (not semantic)
    print("[EmbeddingEngine] Fallback: hash-based embedding.")
    results = []
    for t in texts:
        v = np.array([float((hash(word) % 1000) / 1000) for word in t.split()[:256]])
        if len(v) < 256:
            v = np.pad(v, (0, 256 - len(v)))
        results.append(v.tolist())
    return results


# Initialise when module is loaded
init_model()

? Förklaring
    • Stöd för lokal modell, OpenAI, Ollama, eller hash fallback.
    • Allt är valbart – inget tvingas installeras.
    • Returnerar alltid en lista av vektorer (List[List[float]]).

? Nästa fil:
memory_engine.py – hjärtat i hjärnans minneslager (lagrar text + embedding + metadata, bygger FAISS-index).
Vill du att jag skickar fil 2 nu?
Du sade:
Ja
Code GPT sade:
Grymt ?
Här kommer fil 2 av 4 – memory_engine.py
Detta är själva hjärnans lagrings- och återhämtningssystem — den sparar text, metadata och embeddings, bygger FAISS-index när det finns, och fungerar även utan FAISS (ren SQLite fallback).

? 2 / 4 – memory_engine.py
