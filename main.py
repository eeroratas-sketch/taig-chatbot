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
        "version": "1.4",
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


@app.get("/api/dashboard")
async def dashboard(date: str = None):
    """Päeva vestluste ülevaade - kes mida vaatas, küsis, mida AI vastas."""
    from collections import defaultdict

    target_date = date or datetime.now().strftime("%Y-%m-%d")

    queries_file = os.path.join(config.ANALYTICS_DIR, "queries.jsonl")
    feedback_file = os.path.join(config.ANALYTICS_DIR, "feedback.jsonl")

    sessions = defaultdict(lambda: {"messages": [], "pages": set(), "products": set(), "language": "et", "first_seen": None, "last_seen": None})
    day_stats = {"total_messages": 0, "unique_sessions": 0, "products_viewed": set(), "categories_viewed": set(), "languages": defaultdict(int), "feedback_pos": 0, "feedback_neg": 0, "popular_questions": defaultdict(int)}

    if os.path.exists(queries_file):
        with open(queries_file, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except:
                    continue
                ts = d.get("timestamp", "")
                if not ts.startswith(target_date):
                    continue

                sid = d.get("session_id", "unknown")[:8]
                msg = d.get("message", "")
                resp = d.get("response", "")
                lang = d.get("language", "et")
                page = d.get("page", {})

                day_stats["total_messages"] += 1
                day_stats["languages"][lang] += 1

                s = sessions[sid]
                if not s["first_seen"]:
                    s["first_seen"] = ts
                s["last_seen"] = ts
                s["language"] = lang

                # Lisa vestlus
                entry = {"time": ts[11:19] if len(ts) > 19 else ts, "question": msg[:200]}
                if resp:
                    entry["answer"] = resp[:300]
                s["messages"].append(entry)

                # Lisa tooted/lehed
                if page.get("product"):
                    s["products"].add(page["product"])
                    day_stats["products_viewed"].add(page["product"])
                if page.get("category"):
                    s["pages"].add(page["category"])
                    day_stats["categories_viewed"].add(page["category"])
                if page.get("url"):
                    s["pages"].add(page["url"])

                # Populaarsed küsimused (filtreeri proaktiivsed välja)
                if msg and not msg.startswith("[PROAKTIIVNE"):
                    # Lihtsusta küsimust
                    q = msg.lower().strip()[:80]
                    if len(q) > 5:
                        day_stats["popular_questions"][q] += 1

    # Feedback
    if os.path.exists(feedback_file):
        with open(feedback_file, encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                except:
                    continue
                ts = d.get("timestamp", "")
                if ts.startswith(target_date):
                    if d.get("rating") == "up":
                        day_stats["feedback_pos"] += 1
                    elif d.get("rating") == "down":
                        day_stats["feedback_neg"] += 1

    # Koosta vastus
    sessions_list = []
    for sid, s in sessions.items():
        sessions_list.append({
            "session_id": sid,
            "language": s["language"],
            "first_seen": s["first_seen"],
            "last_seen": s["last_seen"],
            "message_count": len(s["messages"]),
            "products_viewed": list(s["products"]),
            "pages": list(s["pages"])[:10],
            "conversation": s["messages"][:50],
        })

    # Sorteeri viimase aktiivsuse järgi
    sessions_list.sort(key=lambda x: x["last_seen"] or "", reverse=True)

    # Top küsimused
    top_questions = sorted(day_stats["popular_questions"].items(), key=lambda x: x[1], reverse=True)[:20]

    return {
        "date": target_date,
        "summary": {
            "total_messages": day_stats["total_messages"],
            "unique_sessions": len(sessions),
            "products_viewed": list(day_stats["products_viewed"])[:50],
            "categories_viewed": list(day_stats["categories_viewed"])[:20],
            "languages": dict(day_stats["languages"]),
            "feedback": {"positive": day_stats["feedback_pos"], "negative": day_stats["feedback_neg"]},
        },
        "top_questions": [{"question": q, "count": c} for q, c in top_questions],
        "sessions": sessions_list,
    }


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


@app.get("/dashboard")
async def serve_dashboard():
    """Vestluste ülevaate dashboard (HTML)."""
    return FileResponse("static/dashboard.html", media_type="text/html")


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        reload=not os.environ.get("RENDER"),  # Renderis ei kasuta reload
        log_level="info",
    )
