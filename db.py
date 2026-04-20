"""
Postgres DB integratsioon vestluste püsivaks salvestamiseks.
Fallback: kui DATABASE_URL puudub või ühendus luhtub, logitakse lihtsalt JSONL faili.
"""
import json
import logging
import os
import threading
from datetime import datetime

log = logging.getLogger('taig_chatbot.db')

DATABASE_URL = os.environ.get('DATABASE_URL', '').strip()

# psycopg 3 (psycopg) eelistatud; fallback psycopg2-binary
_conn = None
_conn_lock = threading.Lock()
_driver = None

if DATABASE_URL:
    try:
        import psycopg  # psycopg 3
        _driver = 'psycopg3'
    except ImportError:
        try:
            import psycopg2  # psycopg 2
            _driver = 'psycopg2'
        except ImportError:
            log.warning("psycopg/psycopg2 puudub, DB logimine ei tööta")


def _get_conn():
    """Hangi (või loo uuesti) ühendus. Thread-safe."""
    global _conn
    if not DATABASE_URL or not _driver:
        return None
    with _conn_lock:
        try:
            if _conn is None or (hasattr(_conn, 'closed') and _conn.closed):
                if _driver == 'psycopg3':
                    import psycopg
                    _conn = psycopg.connect(DATABASE_URL, autocommit=True)
                else:
                    import psycopg2
                    _conn = psycopg2.connect(DATABASE_URL)
                    _conn.autocommit = True
            return _conn
        except Exception as e:
            log.warning(f"DB ühenduse loomine ebaõnnestus: {e}")
            _conn = None
            return None


def init_schema():
    """Loo tabelid kui pole olemas."""
    if not DATABASE_URL:
        log.info("DATABASE_URL puudub - DB logimine välja lülitatud")
        return False

    conn = _get_conn()
    if not conn:
        return False

    try:
        with conn.cursor() as cur:
            cur.execute("""
                CREATE TABLE IF NOT EXISTS queries (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    session_id TEXT,
                    message TEXT,
                    response TEXT,
                    language TEXT,
                    page_type TEXT,
                    product_name TEXT,
                    product_sku TEXT,
                    product_price TEXT,
                    category_name TEXT,
                    page_url TEXT,
                    raw_page JSONB
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_queries_timestamp ON queries(timestamp DESC)")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_queries_session ON queries(session_id)")

            cur.execute("""
                CREATE TABLE IF NOT EXISTS feedback (
                    id BIGSERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    session_id TEXT,
                    message_id TEXT,
                    rating TEXT,
                    comment TEXT
                )
            """)
            cur.execute("CREATE INDEX IF NOT EXISTS idx_feedback_timestamp ON feedback(timestamp DESC)")
        log.info("DB skeem initsialiseeritud")
        return True
    except Exception as e:
        log.error(f"DB skeemi loomine ebaõnnestus: {e}")
        return False


def log_query(session_id, message, response, language, page_context=None):
    """Salvesta vestluse päring DB-sse. Ei viska errorit - kui DB ei tööta, logitakse ainult hoiatus."""
    if not DATABASE_URL:
        return False

    conn = _get_conn()
    if not conn:
        return False

    try:
        page = page_context or {}
        raw_page = json.dumps(page, ensure_ascii=False) if page else None

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO queries
                    (session_id, message, response, language,
                     page_type, product_name, product_sku, product_price,
                     category_name, page_url, raw_page)
                VALUES
                    (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                session_id[:64] if session_id else None,
                (message or '')[:2000],
                (response or '')[:3000],
                language,
                page.get('page_type'),
                page.get('product_name'),
                page.get('product_sku'),
                page.get('product_price'),
                page.get('category_name'),
                page.get('url'),
                raw_page,
            ))
        return True
    except Exception as e:
        log.warning(f"DB logimine ebaõnnestus: {e}")
        # Ühendus katki - resetime järgmiseks korraks
        global _conn
        with _conn_lock:
            _conn = None
        return False


def log_feedback(session_id, message_id, rating, comment=None):
    """Salvesta feedback DB-sse."""
    if not DATABASE_URL:
        return False
    conn = _get_conn()
    if not conn:
        return False
    try:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO feedback (session_id, message_id, rating, comment)
                VALUES (%s, %s, %s, %s)
            """, (session_id, message_id, rating, comment))
        return True
    except Exception as e:
        log.warning(f"DB feedback logimine ebaõnnestus: {e}")
        return False


def get_dashboard_data(date_from, date_to):
    """Tagasta dashboardile kõik vestlused vahemikus.

    date_from, date_to: 'YYYY-MM-DD' stringid (mõlemad kaasa arvatud)
    """
    if not DATABASE_URL:
        return None
    conn = _get_conn()
    if not conn:
        return None

    try:
        # date_to lõpp on järgmise päeva algus - et hõlmata kogu date_to päev
        with conn.cursor() as cur:
            cur.execute("""
                SELECT timestamp, session_id, message, response, language,
                       page_type, product_name, product_sku, product_price,
                       category_name, page_url
                FROM queries
                WHERE timestamp >= %s::date
                  AND timestamp < (%s::date + INTERVAL '1 day')
                ORDER BY timestamp ASC
            """, (date_from, date_to))
            rows = cur.fetchall()

        queries = []
        for r in rows:
            queries.append({
                'timestamp': r[0].isoformat() if r[0] else None,
                'session_id': r[1],
                'message': r[2],
                'response': r[3],
                'language': r[4],
                'page_type': r[5],
                'product_name': r[6],
                'product_sku': r[7],
                'product_price': r[8],
                'category_name': r[9],
                'page_url': r[10],
            })

        # Feedback
        with conn.cursor() as cur:
            cur.execute("""
                SELECT rating, COUNT(*) FROM feedback
                WHERE timestamp >= %s::date AND timestamp < (%s::date + INTERVAL '1 day')
                GROUP BY rating
            """, (date_from, date_to))
            fb = dict(cur.fetchall())

        return {
            'queries': queries,
            'feedback': {
                'positive': fb.get('up', 0),
                'negative': fb.get('down', 0),
            }
        }
    except Exception as e:
        log.error(f"DB dashboard päring ebaõnnestus: {e}")
        return None
