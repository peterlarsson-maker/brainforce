"""
Context Builder for BrainForce Apollo
Retrieves relevant context (memories) based on semantic similarity.
"""

from typing import List, Dict
from core import memory_engine

MAX_CONTEXT_TOKENS = 2000  # to prevent huge prompts

def get_context(query: str, limit: int = 5, as_text: bool = True) -> str | List[Dict]:
    """
    Retrieve relevant memories for a given query.

    Args:
        query (str): The input text or question.
        limit (int): Number of memory entries to retrieve.
        as_text (bool): Return concatenated text or list of dicts.

    Returns:
        str | List[Dict]: context string or structured data.
    """
    matches = memory_engine.search_memory(query=query, limit=limit)
    if not matches:
        return "" if as_text else []

    if as_text:
        # Concatenate memory texts into a context block
        ctx = "\n\n".join(
            [f"[{m['source']} #{m['id']}] {m['text']}" for m in matches]
        )
        # Trim if too long
        if len(ctx) > MAX_CONTEXT_TOKENS * 5:
            ctx = ctx[:MAX_CONTEXT_TOKENS * 5] + "..."
        return ctx
    else:
        return matches


def learn_from_text(text: str, source: str = "context", tags: List[str] = None):
    """
    Store new information into memory engine.
    This is useful when the system processes or 'learns' from text.
    """
    if not text.strip():
        return
    memory_engine.save_memory(text=text, source=source, tags=tags or [])


def contextual_response(query: str, model_func=None) -> str:
    """
    Generate a response with context.

    Args:
        query (str): User query or topic.
        model_func (callable): Optional function to generate output.
                               Expected signature: func(prompt: str) -> str
    """
    ctx = get_context(query=query, limit=5, as_text=True)
    if not model_func:
        # Fallback response using context only
        return f"Context retrieved ({len(ctx)} chars):\n\n{ctx[:800]}..."

    # Combine query + context for model
    prompt = f"Relevant context:\n{ctx}\n\nUser query:\n{query}\n\nAnswer:"
    return model_func(prompt)

? Förklaring
    • get_context() hämtar semantiskt relevanta minnen.
    • learn_from_text() låter BrainForce lära sig ny information.
    • contextual_response() kan användas för att svara på frågor med kontext — du kan koppla en LLM eller lokal modell här senare.

? Exempel på användning:
from core import context_builder

# Lägg till kunskap
context_builder.learn_from_text("BrainForce uses hybrid FAISS memory.", "system")

# Fråga
print(context_builder.get_context("How does BrainForce store memory?", as_text=True))

? Nästa (sista) fil:
train_scheduler.py – automatiskt “lärande” och underhållsloop som körs i bakgrunden (schemalagd).
Vill du att jag skickar fil 4 nu?
Du sade:
Ja
Code GPT sade:
Snyggt ?
Här kommer sista delen — fil 4 av 4: train_scheduler.py
Det här är hjärnans “autonoma inlärningsloop” som automatiskt matar in nya loggar, händelser eller systemdata i minnet.
Den körs via BrainForce’s befintliga scheduler (apscheduler), så du får självförbättring över tid.

? 4 / 4 – train_scheduler.py
