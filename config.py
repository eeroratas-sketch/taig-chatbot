"""
Taig.ee AI müügiassistendi seadistus.
Keskkonna muutujad: ANTHROPIC_API_KEY, PORT
"""
import os

# Claude API
ANTHROPIC_API_KEY = os.environ.get("ANTHROPIC_API_KEY", "")
CLAUDE_MODEL = "claude-haiku-4-5-20251001"

# Magento
MAGENTO_GRAPHQL_URL = "https://taig.ee/graphql"
STOCK_XML_URL = "https://taig.ee/feeds/kaup24_stock_price.xml"
STORE_BASE_URL = "https://taig.ee/et"

# Cache
CACHE_FILE = "cache/products_cache.json"
CACHE_TTL_HOURS = 6

# Server
PORT = int(os.environ.get("PORT", 8100))
ALLOWED_ORIGINS = ["https://taig.ee", "http://localhost", "http://127.0.0.1"]

# Rate limiting
MAX_REQUESTS_PER_MINUTE = 10
MAX_REQUESTS_PER_HOUR = 30

# Chat
MAX_HISTORY_MESSAGES = 10
SESSION_TIMEOUT_MINUTES = 30
MAX_PRODUCT_CONTEXT = 8  # Mitu toodet korraga Claude'ile saata

# Analytics
ANALYTICS_DIR = "analytics"
SCHOOL_PACK_ENABLED = True
