"""
Taig.ee AI müügiassistendi server.
Käivita: python main.py
"""
import asyncio
import json
import logging
import os
import uuid
from datetime import datetime

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import uvicorn

import config
from product_loader import get_products
from product_search import ProductSearch
from chat_engine import ChatEngine
from rate_limiter import RateLimiter

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(name)s %(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('chatbot.log', encoding='utf-8'),
    ]
)
log = logging.getLogger('taig_chatbot')

# App
app = FastAPI(title="Taig.ee AI Müügiassistent", version="1.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.ALLOWED_ORIGINS + ["*"],  # Dev: luba kõik, prod: piira
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Globals
search_engine = None
chat_engine = None
rate_limiter = RateLimiter()


class ChatRequest(BaseModel):
    session_id: str = ""
    message: str
    page_context: dict = None  # {type, product_name, product_sku, product_price, product_image, category, cart_items}


class ChatResponse(BaseModel):
    session_id: str
    message: str
    products_found: int = 0


@app.on_event("startup")
async def startup():
    global search_engine, chat_engine

    log.info("=== Taig.ee AI Müügiassistent käivitub ===")

    # Laadi tooted
    log.info("Laadin tooteandmeid...")
    products = get_products()

    if not products:
        log.error("TOODETE LAADIMINE EBAONNESTUS! Server käivitub ilma toodeteta.")
        products = []

    # Ehita otsinguindeks
    search_engine = ProductSearch(products)
    stats = search_engine.get_stats()
    log.info(f"Kataloog laetud: {stats['total']} toodet, {stats['in_stock']} laos, {stats['with_image']} pildiga")

    # Initsieeri chat engine
    chat_engine = ChatEngine(search_engine)

    # Loo analytics kaust
    os.makedirs(config.ANALYTICS_DIR, exist_ok=True)

    log.info(f"=== Server valmis portil {config.PORT} ===")


@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, req: Request):
    """Peamine vestluse endpoint."""
    # Rate limit
    client_ip = req.client.host
    allowed, error_msg = rate_limiter.is_allowed(client_ip)
    if not allowed:
        raise HTTPException(status_code=429, detail=error_msg)

    # Valideeri
    message = request.message.strip()
    if not message:
        raise HTTPException(status_code=400, detail="Sõnum on tühi")
    if len(message) > 1000:
        raise HTTPException(status_code=400, detail="Sõnum on liiga pikk (max 1000 tähemärki)")

    # Session
    session_id = request.session_id or str(uuid.uuid4())

    # Chat
    if not chat_engine:
        raise HTTPException(status_code=503, detail="Server alles käivitub...")

    result = chat_engine.chat(session_id, message, page_context=request.page_context)

    return ChatResponse(
        session_id=session_id,
        message=result['message'],
        products_found=result.get('products_found', 0),
    )


@app.get("/api/debug-search")
async def debug_search(q: str = "test"):
    """Debug otsing."""
    from product_search import tokenize, _expand_query
    tokens = tokenize(q)
    expanded = _expand_query(tokens)
    results = search_engine.search(q, max_results=3) if search_engine else []
    return {
        "query": q,
        "tokens": tokens,
        "expanded": list(expanded)[:20],
        "results_count": len(results),
        "results": [{"sku": r["sku"], "name": r["name"]} for r in results],
    }


@app.post("/api/session")
async def create_session():
    """Loo uus sessioon."""
    return {"session_id": str(uuid.uuid4())}


@app.get("/api/health")
async def health():
    """Tervisekontroll."""
    stats = {}
    if search_engine:
        stats['catalog'] = search_engine.get_stats()
    if chat_engine:
        stats['chat'] = chat_engine.get_stats()
    return {
        "status": "ok",
        "version": "1.2",
        "stats": stats,
    }


@app.post("/api/feedback")
async def feedback(request: Request):
    """Salvesta kasutaja tagasiside."""
    data = await request.json()
    entry = {
        "timestamp": datetime.now().isoformat(),
        "session_id": data.get("session_id"),
        "rating": data.get("rating"),
        "message_index": data.get("message_index"),
    }
    feedback_file = os.path.join(config.ANALYTICS_DIR, "feedback.jsonl")
    with open(feedback_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")
    return {"ok": True}


@app.get("/api/analytics")
async def analytics():
    """Simple analytics."""
    # Read feedback stats
    feedback_file = os.path.join(config.ANALYTICS_DIR, "feedback.jsonl")
    pos = neg = 0
    if os.path.exists(feedback_file):
        with open(feedback_file, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                if d.get("rating") == "up":
                    pos += 1
                elif d.get("rating") == "down":
                    neg += 1

    # Read query log stats
    queries_file = os.path.join(config.ANALYTICS_DIR, "queries.jsonl")
    total_queries = 0
    languages = {}
    if os.path.exists(queries_file):
        with open(queries_file, encoding="utf-8") as f:
            for line in f:
                d = json.loads(line)
                total_queries += 1
                lang = d.get("language", "et")
                languages[lang] = languages.get(lang, 0) + 1

    stats = {}
    if search_engine:
        stats['catalog'] = search_engine.get_stats()
    if chat_engine:
        stats['chat'] = chat_engine.get_stats()

    stats['feedback'] = {"positive": pos, "negative": neg}
    stats['languages'] = languages
    stats['total_logged_queries'] = total_queries
    return stats


# Serve static files (widget)
app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/widget.js")
async def serve_widget():
    """Otsetee widget JS-ile."""
    return FileResponse("static/chatbot-widget.js", media_type="application/javascript")


@app.get("/test.html")
async def serve_test():
    """Testimisleht."""
    return FileResponse("test.html", media_type="text/html")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=not os.environ.get("RENDER"),  # Renderis ei kasuta reload
        log_level="info",
    )
