"""
Claude AI vestlusmootor - müügiassistent taig.ee jaoks.
"""
import anthropic
import logging
import time
from datetime import datetime, timedelta

import config

log = logging.getLogger('taig_chatbot.chat')

SYSTEM_PROMPT = """Sa oled taig.ee e-poe sõbralik müügiassistent. Sinu nimi on Taig Abi.

## Poe info
- **Pood:** taig.ee - Eesti e-pood
- **Omanik:** Taig OÜ
- **Sortiment:** Thule kohvrid ja kotid, Case Logic kotid, koolitarbed, kontoritarbed, kirjutusvahendid
- **Keeled:** Teeninda AINULT eesti keeles
- **Valuuta:** EUR (hinnad sisaldavad käibemaksu)
- **Tarne:** Üle Eesti, tasuta tarne alates teatud summast

## Sinu ülesanded
1. Aita klientidel leida sobivaid tooteid
2. Võrdle tooteid ja anna soovitusi
3. Vasta küsimustele toodete kohta (mõõdud, materjalid, omadused)
4. Suuna klient toote lehele ostma

## Reeglid
- Vasta ALATI eesti keeles, isegi kui küsitakse inglise keeles
- Ole lühike ja konkreetne (max 2-3 lõiku)
- ÄRA välja mõtle tooteid ega hindu - kasuta AINULT antud tooteandmeid
- Kui toodet pole laos, ütle seda ausalt aga paku alternatiive
- Kui ei leia sobivat toodet, ütle ausalt et hetkel pole valikus
- Anna ALATI toote link kujul: [Toote nimi](URL)
- Maini alati hinda
- Kui toode on soodustusega, maini ka tavahinda
- Ole sõbralik ja abivalmis, aga mitte liiga jutustav
- Ära küsi liiga palju küsimusi - paku kohe lahendusi

## Toodete kuvamine
Kui soovitad tooteid, kasuta seda formaati:
**Toote nimi** - HIND €
Lühike kirjeldus (1 lause)
[Vaata toodet →](link)

## Laos info
- "Laos" = saadaval ja kohe tellitav
- "Otsas" = hetkel ei ole saadaval
"""


def _format_product_for_context(product):
    """Vorminda toode Claude kontekstiks."""
    parts = [
        f"SKU: {product['sku']}",
        f"Nimi: {product['name']}",
        f"Hind: {product['price']:.2f} EUR",
    ]
    if product.get('on_sale') and product.get('regular_price'):
        parts.append(f"Tavahind: {product['regular_price']:.2f} EUR (SOODUSTUS!)")
    parts.append(f"Laos: {'Jah ({} tk)'.format(product['qty']) if product['in_stock'] else 'EI - otsas'}")
    if product.get('brand'):
        parts.append(f"Bränd: {product['brand']}")
    if product.get('main_category'):
        parts.append(f"Kategooria: {product['main_category']}")
    if product.get('sub_category'):
        parts.append(f"Alamkategooria: {product['sub_category']}")
    if product.get('short_description'):
        parts.append(f"Kirjeldus: {product['short_description'][:300]}")
    if product.get('url'):
        parts.append(f"Link: {product['url']}")
    if product.get('image_url'):
        parts.append(f"Pilt: {product['image_url']}")
    return '\n'.join(parts)


class ChatEngine:
    def __init__(self, search_engine):
        self.client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
        self.search = search_engine
        self.sessions = {}  # session_id -> {messages, last_activity}
        self.total_queries = 0
        self.total_tokens = 0

    def _cleanup_sessions(self):
        """Eemalda aegunud sessioonid."""
        now = datetime.now()
        expired = [
            sid for sid, data in self.sessions.items()
            if now - data['last_activity'] > timedelta(minutes=config.SESSION_TIMEOUT_MINUTES)
        ]
        for sid in expired:
            del self.sessions[sid]
        if expired:
            log.info(f"Eemaldatud {len(expired)} aegunud sessiooni")

    def _get_session(self, session_id):
        """Hangi või loo sessioon."""
        self._cleanup_sessions()
        if session_id not in self.sessions:
            self.sessions[session_id] = {
                'messages': [],
                'last_activity': datetime.now(),
            }
        session = self.sessions[session_id]
        session['last_activity'] = datetime.now()
        return session

    def chat(self, session_id, user_message):
        """Töötle kasutaja sõnum ja tagasta vastus."""
        session = self._get_session(session_id)

        # 1. Otsi relevantsed tooted
        search_results = self.search.search(user_message, max_results=config.MAX_PRODUCT_CONTEXT)

        # 2. Koosta kontekst
        if search_results:
            product_context = "LEITUD TOOTED (kasuta neid vastamiseks):\n\n"
            for i, p in enumerate(search_results, 1):
                product_context += f"--- Toode {i} ---\n"
                product_context += _format_product_for_context(p)
                product_context += "\n\n"
        else:
            product_context = "OTSINGUGA EI LEITUD ÜHTEGI SOBIVAT TOODET. Ütle kliendile, et hetkel sellist toodet valikus ei ole.\n"

        # 3. Lisa kasutaja sõnum koos kontekstiga
        enriched_message = f"{user_message}\n\n---\n{product_context}"

        # 4. Ehita sõnumite ajalugu
        messages = list(session['messages'])  # koopia
        messages.append({"role": "user", "content": enriched_message})

        # Piira ajaloo pikkust
        if len(messages) > config.MAX_HISTORY_MESSAGES:
            messages = messages[-config.MAX_HISTORY_MESSAGES:]

        # 5. Saada Claude'ile
        try:
            response = self.client.messages.create(
                model=config.CLAUDE_MODEL,
                max_tokens=800,
                system=SYSTEM_PROMPT,
                messages=messages,
            )

            assistant_message = response.content[0].text

            # Uuenda statistikat
            self.total_queries += 1
            self.total_tokens += response.usage.input_tokens + response.usage.output_tokens

            # Salvesta ajalukku (ilma toote kontekstita, et mälu kokku hoida)
            session['messages'].append({"role": "user", "content": user_message})
            session['messages'].append({"role": "assistant", "content": assistant_message})

            # Piira ajaloo pikkust
            if len(session['messages']) > config.MAX_HISTORY_MESSAGES:
                session['messages'] = session['messages'][-config.MAX_HISTORY_MESSAGES:]

            log.info(f"Vastatud: session={session_id[:8]}, tokens={response.usage.input_tokens}+{response.usage.output_tokens}")

            return {
                'message': assistant_message,
                'products_found': len(search_results),
            }

        except Exception as e:
            log.error(f"Claude API viga: {e}")
            return {
                'message': 'Vabandust, tekkis tehniline viga. Palun proovige uuesti!',
                'products_found': 0,
                'error': True,
            }

    def get_stats(self):
        return {
            'total_queries': self.total_queries,
            'total_tokens': self.total_tokens,
            'active_sessions': len(self.sessions),
        }
