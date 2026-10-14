"""
Per-user rate limits for the routes that spend external quota
(/chat → HuggingFace rephrase, /investments/search → mfapi.in).

Keyed on the verified Supabase user (set by auth.token_claims), falling back
to the client IP. In-memory storage: fine for one process; Phase 4 revisits
this for multiple workers and X-Forwarded-For behind a proxy.
"""
import os

from fastapi import Request
from slowapi import Limiter
from slowapi.util import get_remote_address

CHAT_LIMIT = os.getenv("RATE_LIMIT_CHAT", "20/minute")
SEARCH_LIMIT = os.getenv("RATE_LIMIT_SEARCH", "30/minute")


def rate_key(request: Request) -> str:
    return getattr(request.state, "rate_key", None) or f"ip:{get_remote_address(request)}"


limiter = Limiter(key_func=rate_key)
