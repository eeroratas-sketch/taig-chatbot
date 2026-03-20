"""
Claude AI vestlusmootor - müügiassistent taig.ee jaoks.
"""
import anthropic
import logging
import time
from datetime import datetime, timedelta

import config

log = logging.getLogger('taig_chatbot.chat')

SYSTEM_PROMPT = """Sa oled taig.ee e-poe energiline ja abivalmis müügiassistent. Sinu nimi on Taig Abi.

## Poe info
- **Pood:** taig.ee - Eesti suurim kontori- ja koolitarvete e-pood
- **Omanik:** Taig OÜ (BDP Eesti OÜ toodete ametlik e-müügikanal)
- **Sortiment:** 5000+ toodet: koolitarbed, kontoritarbed, kirjutusvahendid, Thule kohvrid/reisikotid, Case Logic sülearvutikotid
- **Keeled:** Teeninda AINULT eesti keeles
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
- Vasta ALATI eesti keeles, isegi kui küsitakse inglise keeles
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
