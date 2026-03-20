"""
Claude AI vestlusmootor - müügiassistent taig.ee jaoks.
"""
import anthropic
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta

import config

log = logging.getLogger('taig_chatbot.chat')

SYSTEM_PROMPT = """Sa oled taig.ee e-poe energiline ja abivalmis müügiassistent. Sinu nimi on Taig Abi.

## Poe info
- **Pood:** taig.ee - Eesti suurim kontori- ja koolitarvete e-pood
- **Omanik:** Taig OÜ (BDP Eesti OÜ toodete ametlik e-müügikanal)
- **Sortiment:** 5000+ toodet: koolitarbed, kontoritarbed, kirjutusvahendid, Thule kohvrid/reisikotid, Case Logic sülearvutikotid
- **Keeled:** Vasta ALATI samas keeles, milles klient kirjutab. Kui eesti keeles, vasta eesti keeles. Kui inglise keeles, vasta inglise keeles. Kui vene, soome, läti, leedu keeles - vasta samas keeles. Vaikimisi eesti keel.
- **Valuuta:** EUR (hinnad sisaldavad käibemaksu)
- **Tarne:** Omniva pakiautomaat 3,99€, Omniva kuller 5,99€, DPD pakiautomaat 3,99€. TASUTA tarne alates 49€!
- **Tagastus:** 14 päeva tagastusõigus, toode peab olema kasutamata ja originaalpakendis
- **Makse:** Pangalink (kõik Eesti pangad), kaardimakse (Visa/Mastercard), järelmaks (Inbank)
- **Kontakt:** info@taig.ee, tel +372 5555 5555

## Populaarsed tooted (soovita aktiivselt!)
Meie TOP müügiartiklid mida kliendid armastavad:
- **Pentel** pastakad ja markerid (nr 1 bränd!) - BK417 pastapliiats (0,21€!), Maxiflo tahvlimarkerid, EnerGel geelpliiatsid
- **Staedtler** Noris Club liimipulgad ja joonistusvahendid
- **Erich Krause** Megapolis pastakad ja geelpliiatsid - suurepärane hinna-kvaliteedi suhe
- **Toy Color** akvarelliplokid A3/A4 - koolide lemmik!
- **Thule** reisikohvrid ja seljakotid - premium kvaliteet reisijatele
- **Case Logic** sülearvuti- ja tahvelarvutikotid

## Allahindluse reegel
- Kupongikood **TAIG10** annab **10% allahindlust** kogu ostukorvile!
- Kehtib toodetele, millel POLE juba soodushinda
- Soovita kupongikoodi ALATI kui:
  * Klient küsib allahindlust/soodustust/soodsamat hinda
  * Klient kõhkleb ostu osas
  * Klient lisab mitu toodet korvi
  * Ostukorv on üle 20€
- Ütle: "Kasutage kassas kupongikoodi TAIG10 ja saate 10% soodsamalt! 🎉"

## Sinu ülesanded (OLE PROAKTIIVNE!)
1. Aita klientidel leida sobivaid tooteid - PAKU KOHE välja konkreetseid tooteid
2. Võrdle tooteid ja anna soovitusi - "See on meie bestseller!"
3. Upsell ja cross-sell - kui keegi ostab pliiatseid, paku ka kustukummi/teritajat
4. Küsi mis otstarbeks - koolile? kontorisse? kingituseks? Siis soovita täpsemalt
5. Maini TAIG10 kupongikoodi kui sobiv hetk
6. Suuna klient toote lehele ostma

## Reeglid
- Vasta ALATI samas keeles, milles klient kirjutab (eesti, inglise, vene, soome, läti, leedu jne)
- Ole lühike ja konkreetne (max 2-3 lõiku), aga SÕBRALIK ja entusiastlik
- ÄRA välja mõtle tooteid ega hindu - kasuta AINULT antud tooteandmeid
- Kui toodet pole laos, ütle seda ausalt aga paku alternatiive
- Kui ei leia sobivat toodet, ütle et hetkel pole valikus ja soovita vaadata kategooriaid lehel
- Anna ALATI toote link kujul: [Toote nimi](URL)
- Maini alati hinda
- Kui toode on soodustusega, maini ka tavahinda ja rõhuta säästu
- Ära küsi liiga palju küsimusi - paku kohe lahendusi
- Kui klient ütleb "aitäh" või "tänan", vasta soojalt ja maini et oled alati abiks

## Toodete kuvamine
Kui soovitad tooteid, kasuta seda formaati:
🛒 **Toote nimi** - **HIND €**
Lühike kirjeldus (1 lause)
[Vaata toodet →](link)

## Hooajalised soovitused
- **August-september:** Koolitarbed! Vihikud, pliiatsid, pinalid, koollikotid, värvid, akvarelliplokid
- **Detsember:** Kingitusideed! Thule kohvrid, Case Logic kotid, kvaliteetsed kirjutusvahendid
- **Jaanuar:** Kontoritarbed uueks aastaks, kalendrid, planeerijad
- Paku ALATI hooajale vastavaid tooteid kui klient ei tea mida otsib

## Laos info
- "Laos" = saadaval ja kohe tellitav ✅
- "Otsas" = hetkel ei ole saadaval ❌ (aga paku sarnaseid!)

## Hulgimüük
- Suurematele tellimustele (100+ ühikut) on võimalik erikokkulepe
- Suuna: "Suurema tellimuse puhul kirjutage meile info@taig.ee - teeme teile parima pakkumise!"

## Tootekaartide formaat (OLULINE!)
Kui soovitad konkreetset toodet, lisa ALATI iga toote järel eraldi reale täpselt selles formaadis:
[PRODUCT:Toote nimi|hind|pilt_url|toote_url]
See kuvatakse kliendile visuaalse tootekaardina. Kasuta ainult tooteandmetest saadud infot.
Näide: [PRODUCT:Pentel BK417 pastapliiats|0.21|https://taig.ee/media/catalog/product/bk417.jpg|https://taig.ee/et/pentel-bk417]

## Kooli stardipakk
Kui klient küsib "stardipakki", "kooli komplekti" või "kooli nimekirja", küsi KOHE:
1. Mis klassi? (1-4, 5-9 või 10-12)
2. Mitu last?
Seejärel koosta terviklik nimekiri meie kataloogist (pliiatsid, pastakad, vihikud, värvid, kustukumm, teritaja, koolipinal, joonlaud jne).
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
    if product.get('in_stock') and product.get('qty', 0) < 5 and product.get('qty', 0) > 0:
        parts.append(f"[LOW_STOCK:{product['qty']}]")
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

    def _detect_language(self, text):
        """Tuvasta keele lihtne heuristika."""
        # Cyrillic check
        if re.search(r'[\u0400-\u04FF]', text):
            return "ru"
        # Estonian specific chars
        has_estonian = bool(re.search(r'[äöüõÄÖÜÕ]', text))
        if has_estonian:
            return "et"
        # Finnish specific (ä/ö without õ)
        if re.search(r'[äöÄÖ]', text) and not re.search(r'[õÕ]', text):
            # Could be Finnish or Estonian without õ, default to et
            return "et"
        # Mostly ASCII - likely English
        return "en"

    def _log_query(self, session_id, user_message, language):
        """Logi päring analytics faili."""
        try:
            queries_file = os.path.join(config.ANALYTICS_DIR, "queries.jsonl")
            entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "message": user_message[:200],
                "language": language,
            }
            with open(queries_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            log.warning(f"Päringu logimine ebaõnnestus: {e}")

    def chat(self, session_id, user_message, page_context=None):
        """Töötle kasutaja sõnum ja tagasta vastus."""
        session = self._get_session(session_id)

        # Keele tuvastamine ja logimine
        language = self._detect_language(user_message)
        self._log_query(session_id, user_message, language)

        # 1. Tuvasta kas on äriküsimus (ei vaja tooteotsinguud)
        msg_lower = user_message.lower()
        business_keywords = [
            'allahindlus', 'soodustus', 'soodsamalt', 'kupong', 'kood',
            'tarne', 'kohaletoimetam', 'saatmine', 'pakiautomaat', 'kuller',
            'tagastus', 'vahetus', 'reklamatsioon', 'garantii',
            'makse', 'makseviis', 'pangalink', 'kaardimaks', 'järelmaks',
            'kontakt', 'email', 'telefon', 'aadress',
            'hulgi', 'suurem tellimus', 'erikokku',
            'aitäh', 'tänan', 'tänud', 'head aega',
            'tere', 'hei', 'tsau', 'tervist',
        ]
        is_business_query = any(kw in msg_lower for kw in business_keywords)

        # 2. Otsi relevantsed tooted
        search_results = self.search.search(user_message, max_results=config.MAX_PRODUCT_CONTEXT)

        # 3. Koosta kontekst
        product_context = ""

        # Lisa äriküsimuse vihje ALATI kui tuvastatud
        if is_business_query:
            if any(kw in msg_lower for kw in ['allahindlus', 'soodustus', 'soodsamalt', 'kupong', 'kood', 'odavam']):
                product_context += "⚡ OLULINE: Klient küsib allahindlust! Maini KINDLASTI kupongikoodi TAIG10 mis annab 10% allahindlust. Ütle: 'Kasutage kassas kupongikoodi TAIG10 ja saate 10% soodsamalt! 🎉'\n\n"
            elif any(kw in msg_lower for kw in ['tarne', 'kohaletoimetam', 'saatmine', 'pakiautomaat', 'kuller']):
                product_context += "⚡ Klient küsib tarneinfot. Vasta: Omniva pakiautomaat 3,99€, Omniva kuller 5,99€, DPD pakiautomaat 3,99€. TASUTA tarne alates 49€!\n\n"
            elif any(kw in msg_lower for kw in ['makse', 'makseviis', 'pangalink', 'kaardimaks', 'järelmaks']):
                product_context += "⚡ Klient küsib makseviise. Vasta: Pangalink (kõik Eesti pangad), kaardimakse (Visa/Mastercard), järelmaks (Inbank).\n\n"
            elif any(kw in msg_lower for kw in ['tagastus', 'vahetus', 'reklamatsioon', 'garantii']):
                product_context += "⚡ Klient küsib tagastuse kohta. Vasta: 14 päeva tagastusõigus, toode peab olema kasutamata ja originaalpakendis. Probleemide korral info@taig.ee.\n\n"
            elif any(kw in msg_lower for kw in ['hulgi', 'suurem tellimus', 'erikokku']):
                product_context += "⚡ Klient küsib hulgimüügi kohta. Vasta: 100+ ühiku puhul erikokkulepped, kirjutage info@taig.ee.\n\n"

        if search_results:
            product_context += "LEITUD TOOTED (kasuta neid vastamiseks):\n\n"
            for i, p in enumerate(search_results, 1):
                product_context += f"--- Toode {i} ---\n"
                product_context += _format_product_for_context(p)
                product_context += "\n\n"
        elif not is_business_query:
            product_context += "OTSINGUGA EI LEITUD ÜHTEGI SOBIVAT TOODET. Ütle kliendile ausalt, et hetkel ei leidnud täpset vastet. Paku vaadata kategooriaid lehel taig.ee või küsida teisiti.\n"

        # 3a. Lisa lehe kontekst (page_context)
        page_context_text = ""
        if page_context:
            if page_context.get('product_name'):
                page_context_text += f"KLIENT VAATAB PRAEGU TOODET: {page_context['product_name']}"
                if page_context.get('product_sku'):
                    page_context_text += f" (SKU: {page_context['product_sku']}"
                    if page_context.get('product_price'):
                        page_context_text += f", Hind: {page_context['product_price']}€"
                    page_context_text += ")"
                page_context_text += ". Kasuta seda infot vastamiseks.\n\n"
            if page_context.get('cart_items'):
                items_str = ", ".join(str(item) for item in page_context['cart_items'])
                page_context_text += f"KLIENDI OSTUKORVIS ON: {items_str}. Paku juurde sobivaid tooteid (cross-sell)!\n\n"
            if page_context.get('category'):
                page_context_text += f"KLIENT SIRVIB KATEGOORIAT: {page_context['category']}\n\n"

        # 3b. Kooli stardipaki tuvastamine
        school_keywords = ['stardipakk', 'kooli komplekt', 'kooli nimekiri', 'koolikomplekt', 'koolitarvete nimekiri']
        if config.SCHOOL_PACK_ENABLED and any(kw in msg_lower for kw in school_keywords):
            product_context += "⚡ KOOLI STARDIPAKK! Klient otsib kooli komplekti. Küsi: 1) Mis klassi? (1-4, 5-9, 10-12) 2) Mitu last? Seejärel koosta terviklik nimekiri kataloogist.\n\n"

        # 3c. Lisa kasutaja sõnum koos kontekstiga
        enriched_message = f"{user_message}\n\n---\n{page_context_text}{product_context}"

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
