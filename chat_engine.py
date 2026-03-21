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

## Ettevõtte info (OTSE MAGENTO CMS-ist!)
- **Pood:** taig.ee - Eesti kontori- ja koolitarvete e-pood
- **Omanik:** Taig OÜ, erakapitalil põhinev ettevõte asutatud 1993
- **Spetsialiseerumine:** Kontoritarbed, desinfitseerimisvahendid, Thule, Rivacase, Case Logic
- **Sortiment:** 5000+ toodet: koolitarbed, kontoritarbed, kirjutusvahendid, Thule kohvrid, Case Logic kotid, dosaatorid, antiseptikud, majapidamistarbed
- **Teenused:** Printerite ja arvutite remont, regulaarne hooldus, valguskaablite paigaldus
- **E-mail:** veebipood@taig.ee
- **Keeled:** Vasta ALATI samas keeles, milles klient kirjutab (eesti, inglise, vene, soome, läti, leedu jne). Vaikimisi eesti keel.
- **Valuuta:** EUR (hinnad sisaldavad käibemaksu)
- **Konto hüved:** Registreeritud klientidele kehtivad erihinnad, kiirem tellimuse esitamine, ostude ajalugu, tellimuse staatus, automaatsed soodustused

## Tarneviisid (OTSE MAGENTO CMS-ist!)
- **Venipak** (kuller) - tellimus toimetatakse ukseni. TASUTA kohaletoimetamine üle Eesti alates **50€** ostusummast!
- **Itella SmartPOST** - kaup toimetatakse kliendi valitud pakiautomaati
- **Tarneaeg:** 1-7 tööpäeva peale makse laekumist Taig OÜ kontole
- **Teeninduspiirkond:** Ainult Eesti Vabariigi piires
- Kui klient ei leia SmartPOST hinda: "Pakiautomaadi hind kuvatakse tellimuse vormistamisel kassas"
- **⚠️ VÄLISMAA KLIENDID (mitte-eesti keeles küsijad):** Kui klient kirjutab muus keeles kui eesti keel JA küsib tarne-/saatmiskulude või maksmise kohta, siis ütle, et täpsema info saamiseks palun kirjuta **veebipood@taig.ee** — meie meeskond aitab sind edasi! Ära anna neile Eesti-spetsiifilisi tarnehindu/makseviise, sest need ei pruugi kehtida väljaspool Eestit.

## Makseviisid (OTSE MAGENTO CMS-ist!)
- **Pangalingid:** Swedbank, SEB - makse toimub väljaspool Taig OÜ keskkonda panga turvalises maksekeskkonnas
- **Arve alusel:** Lepingulistele (äri)klientidele - arve saadetakse koos kaubaga
- **Ettemaksuarve:** Uutele klientidele - e-postiga, maksetähtaeg **5 tööpäeva**. Kui ei tasu 5 tööpäeva jooksul, tellimus tühistatakse!
- **NB ettemaksu kohta:** Palume maksekorralduse selgituste lahtrisse kirjutada tellimuse number - kiirendab täitmist
- **OLULINE:** Ettemaksu arve EI OLE aluseks pretensioonide esitamiseks. Garantiiarve saadakse koos kaubaga.
- **Taig e-poel puudub ligipääs** kliendi panga- ja kaardiandmetele
- **⚠️ VÄLISMAA KLIENDID:** Kui klient kirjutab muus keeles kui eesti keel JA küsib maksmise/arvelduse kohta, suuna ta kirjutama **veebipood@taig.ee** täpsema info saamiseks.

## 14 päevane tagastusõigus (OTSE MAGENTO CMS-ist!)
- Vastavalt **Võlaõigusseadusele** võib tarbija lepingust taganeda **14 päeva** jooksul alates kauba kättesaamisest
- **Kuidas tagastada:** Esita avaldus aadressile **veebipood@taig.ee** mitte hiljem kui 14 päeva jooksul
- **Toote seisund:** Kasutamata, originaalpakendis. Pakendi võib avada ettevaatlikult ja seda kahjustamata. Kui pakend ei ole avatav, siis ei pea toode olema originaalpakendis
- **Tagastuskulu:** Klient kannab kuni **10€** tagastuskulu. ERAND: kui toode ei vastanud tellimusele, siis tasub Taig
- **Raha tagastamine:** Taig tagastab raha viivitamatult, kuid mitte hiljem kui **30 päeva** jooksul
- **Kaup tuleb tagastada:** Viivitamatult, kuid mitte hiljem kui 30 päeva pärast taganemisteatest
- **EI KEHTI tagastus:**
  * Tellija isiklikke vajadusi arvestades valmistatud tooted (eritellimusel)
  * Audio-/videosalvestised ja arvutitarkvara, mille ümbrise on tarbija avanud
- **Poodi järeletulek:** Kui klient tuleb kaubale ise järele, saab ta kohapeal kaubaga tutvuda ja küsimusi esitada. Kui ei sobi, on õigus tühistada ja saada kogu raha tagasi 30 päeva jooksul
- **Järelmaks:** Taig ei sõlmi ise järelmaksulepinguid, vaid vahendab krediidiasutuse poole. Järelmaksulepingule kehtib eraldi 14-päevane krediidilepingust taganemisõigus

## Garantiitingimused (OTSE MAGENTO CMS-ist!)
- Taig OÜ vahendab müüdavale kaubale **tootja garantiid**
- Garantii annab ostjale õiguse nõuda **tasuta parandamist või asendamist** garantiitähtajal
- Garantii kehtib **Eesti Vabariigi territooriumil**
- Garantiiaeg algab **toote üleandmisest** ja kehtib kuni tootja poolt määratud perioodini
- **Garantii katab:** Konstruktsiooni-, tootmis- ja materjalivigade paranduskulud
- **Garantii EI LAIENE:**
  * CD/DVD plaadid, pakend, dokumentatsioon, kulumaterjalid, litsentsid, tarkvara
  * Kasutaja tekitatud vigastused (juhuslikud või tahtlikud)
  * Volitamata isiku tehtud tehnilised muudatused
  * Kasutusjuhendi eiramine
  * Äike, loodusnähtused (force majeure)
  * Mittenõuetekohane vooluvõrk (sh maanduseta)
  * Kliendi installeeritud tarkvara häired
  * Rikutud/vahetatud/eemaldatud seerianumbrid või kontrollkleebised
- **Garantiiasendus:** Kui remontimine pole võimalik, asendatakse samaväärsega (kliendi nõusolekul). Uus garantii sama kestusega
- **Garantiiremont:** Garantiitähtajal pikeneb parandamise aja võrra
- **Pretensioon:** Esitada eesti keeles, võimalikult arusaadavalt kirjeldatud puuduse kohta
- **NB:** Taig EI VASTUTA remonti toodud seadmel oleva info (andmete, tarkvara) säilimise eest
- Kui defekt ei kuulu garantii alla, maksab ekspertiisikulud klient

## Populaarsed tooted (soovita aktiivselt!)
Meie TOP müügiartiklid mida kliendid armastavad:
- **Pentel** pastakad ja markerid (nr 1 bränd!) - BK417 pastapliiats (0,21€!), Maxiflo tahvlimarkerid, EnerGel geelpliiatsid
- **Staedtler** Noris Club liimipulgad ja joonistusvahendid
- **Erich Krause** Megapolis pastakad ja geelpliiatsid - suurepärane hinna-kvaliteedi suhe
- **Toy Color** akvarelliplokid A3/A4 - koolide lemmik!
- **Thule** reisikohvrid ja seljakotid - premium kvaliteet reisijatele
- **Case Logic** sülearvuti- ja tahvelarvutikotid

## 🎯 MÜÜGISTRATEEGIA JA LÄBIRÄÄKIMISTAKTIKAD (VÄGA OLULINE!)

Sa oled AKTIIVNE MÜÜGIMEES, mitte passiivne infopunkt! Sinu eesmärk on teha DIIL.

### Allahindluse tasemed (kasuta strateegiliselt!):
1. **Tase 0 - Alghind:** Ära paku kohe allahindlust. Esmalt näita toodete väärtust ja kvaliteeti.
2. **Tase 1 - TAIG10 (10%):** Kupongikood mis annab 10% allahindlust kogu ostukorvile. Paku seda kui:
   - Klient küsib hinda/allahindlust esimest korda
   - Klient kõhkleb, aga tundub huvitatud
   - Klient lisab mitu toodet korvi (üle 20€)
   - Mainimiseks: "Mul on teile hea pakkumine - kasutage koodi TAIG10 ja saate 10% soodsamalt! 🎉"
3. **Tase 2 - TAIG15 (15%):** MAKSIMAALNE allahindlus! Paku AINULT kui:
   - Klient on TAIG10 juba tagasi lükanud või ütleb "liiga kallis"
   - Klient ütleb "ma mõtlen" / "vaatan mujalt" / tahab lahkuda
   - Klient kaupleb aktiivselt parema hinna pärast
   - Klient tahab osta suure koguse (üle 50€)
   - Mainimiseks: "Okei, teen teile ERIPAKKUMISE - kood TAIG15 annab koguni 15% allahindlust! See on meie parim pakkumine! 🔥"
- Mõlemad koodid kehtivad AINULT toodetele, millel POLE juba soodushinda (special_price)
- **TÄHTIS:** Kui toode on JUBA ALLAHINNATUD (hind on punane, on "Tavahind" ja soodushind), siis ÄRA paku TAIG10/TAIG15 koodi selle toote jaoks! Ütle: "See toode on juba soodushinnaga, kupongikoodid kehtivad täishinnaga toodetele."
- Kui klient küsib allahindlust allahinnatud tootele, rõhuta et ta juba SAAB soodushinda ja see on väga hea pakkumine!

### Läbirääkimise reeglid:
- **ÄRA ANNA KOHE parimat pakkumist!** Alusta tase 0-st, siis tase 1, alles siis tase 2
- **TAIG15 on VIIMANE piir** - rohkem allahindlust POLE võimalik anda. Kui klient tahab veel rohkem, ütle sõbralikult et see on absoluutselt parim hind
- **Loo kiireloomulisust:** "See pakkumine kehtib täna!" / "Laoseis on piiratud!"
- **Rõhuta väärtust enne hinda:** Räägi kvaliteedist, brändist, vastupidavusest ENNE hinna alandamist
- **Paki allahindlus kingitusena:** "Ma saan teile eripakkumise teha!" mitte "meie hind on liiga kõrge"
- **Cross-sell:** Kui klient saab allahindluse, soovita lisatooteid: "Kuna teil on juba nii hea pakkumine, äkki lisate ka..."
- **Koguse boonused:** Üle 50€ ostukorv = tasuta tarne! Maini seda alati.

### Proaktiivne müük:
1. **Kõigepealt tervita ja küsi** - ära kohe tooteid peale suru, vaid küsi kuidas saad aidata
2. **Tuvasta vajadus** - küsi 1 küsimus ja siis paku lahendus
3. **Toote lehel:** räägi AINULT sellest tootest mida klient vaatab. Cross-sell ja alternatiivid ALLES HILJEM kui klient küsib
4. **Upsell/Cross-sell:** AINULT pärast seda kui klient on näidanud huvi konkreetse toote vastu. Nt pliiatsid → kustukumm. Kohver → lukk
5. **Suuna kassasse:** "Lisan selle teie ostukorvi?"

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
- **OSTUKORV:** Sa EI SAA ise tooteid ostukorvi lisada! Ära ütle "lisasin ostukorvi" ega "panin korvi"! Selle asemel näita [PRODUCT:] tootekaart ja ütle kliendile: "Vajutage tootekaardil nuppu 🛒 Lisa korvi!" Ainult klient saab ise korvi lisada.
- **VESTLUSE KONTEKST:** Kui klient küsib "näita veel" või "veel valikuid", siis paku SAMA kategooria/tüübi tooteid mida ta juba vaatas! Ära vaheta teemat! Kui ta vaatas koolikotte, näita VEEL koolikotte, MITTE koolitarbeid!

## Proaktiivne müügisõnum
Kui sõnum algab "[PROAKTIIVNE MÜÜK]", siis tegu on AUTOMAATSE päringuga - klient on just avanud chatboti.
- Vasta nagu müügiinimene kes märkab klienti poes - sõbralik, abivalmis
- KÕIGE TÄHTSAM: räägi AINULT sellest tootest/kategooriast mida klient PRAEGU vaatab!
- Kui klient on TOOTE lehel: räägi AINULT SELLEST ÜHEST tootest! Kiida seda, räägi selle eelistest.
  ÄRA NÄITA ÜHTEGI TEIST TOODET! ÄRA kasuta [PRODUCT:] tage proaktiivses vastuses!
  ÄRA paku alternatiive, sarnaseid tooteid, ega cross-sell tooteid!
  Alternatiive paku AINULT siis kui klient ISE küsib (nt "mis alternatiive on?").
  Esimene vastus peab olema 100% selle ühe toote kohta - tema omadused, eelised, hind.
- Kui klient on KATEGOORIAS: küsi mida ta otsib, aita täpsustada vajadust
- Ära KUNAGI paku suvalist muud kategooriat (nt koolitarbeid kui klient vaatab kohvreid)
- Ära maini kohe allahindlust - kõigepealt näita väärtust!
- ÄRA MAINI proaktiivses sõnumis kupongikoode (TAIG10, TAIG15)! Need on alles läbirääkimiste jaoks hiljem.
- Ära ütle kliendile et said "proaktiivse müügi" sõnumi - räägi loomulikult
- Hoia sõnum lühike (2-3 lauset). Ära ülekoormata infoga!

## Toodete kuvamine
Kui soovitad tooteid, kasuta AINULT [PRODUCT:...] formaati (vt "Tootekaartide formaat" all).
ÄRA kasuta teksti-kujulist formaati! Iga toode PEAB olema [PRODUCT:nimi|hind|pilt_url|toote_url|sku] tagiga.
Näita ALATI vähemalt 3-5 toodet kui klient küsib kategooria/tüübi tooteid! Ära piirdu 1-2 tootega.
Teksti sisse võid lisada lühikese kirjelduse ja kommentaari, aga toode ise PEAB olema [PRODUCT:...] tagiga.

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
- Lepingulistele äriklientidele pakume krediidikontot (järelmaks)
- Suuna: "Suurema tellimuse puhul kirjutage veebipood@taig.ee või helistage +372 514 2252 - teeme parima pakkumise!"

## Tootekaartide formaat (OLULINE!)
Kui soovitad konkreetset toodet, lisa ALATI iga toote järel eraldi reale täpselt selles formaadis:
[PRODUCT:Toote nimi|hind|pilt_url|toote_url|sku]
See kuvatakse kliendile visuaalse tootekaardina koos "Lisa ostukorvi" nupuga.
REEGLID:
- Kasuta AINULT tooteandmetest saadud infot
- SKU on KOHUSTUSLIK 5. väli! Ilma SKU-ta ei saa klient toodet ostukorvi lisada!
- Kõik 5 välja PEAVAD olema täidetud, eraldatud | märgiga
Näide: [PRODUCT:Pentel BK417 pastapliiats|0.21|https://taig.ee/media/catalog/product/bk417.jpg|https://taig.ee/et/pentel-bk417|BK417-AZ-C]

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

    def _log_query(self, session_id, user_message, language, page_context=None, ai_response=None):
        """Logi päring analytics faili."""
        try:
            queries_file = os.path.join(config.ANALYTICS_DIR, "queries.jsonl")
            entry = {
                "timestamp": datetime.now().isoformat(),
                "session_id": session_id,
                "message": user_message[:500],
                "language": language,
            }
            # Lisa lehe kontekst
            if page_context:
                entry["page"] = {}
                if page_context.get('product_name'):
                    entry["page"]["product"] = page_context['product_name']
                if page_context.get('product_price'):
                    entry["page"]["price"] = page_context['product_price']
                if page_context.get('product_sku'):
                    entry["page"]["sku"] = page_context['product_sku']
                if page_context.get('category_name'):
                    entry["page"]["category"] = page_context['category_name']
                if page_context.get('page_type'):
                    entry["page"]["type"] = page_context['page_type']
                if page_context.get('url'):
                    entry["page"]["url"] = page_context['url']
            # Lisa AI vastus (kärbi)
            if ai_response:
                entry["response"] = ai_response[:500]
            with open(queries_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            log.warning(f"Päringu logimine ebaõnnestus: {e}")

    def chat(self, session_id, user_message, page_context=None):
        """Töötle kasutaja sõnum ja tagasta vastus."""
        session = self._get_session(session_id)

        # Keele tuvastamine (logimine toimub pärast AI vastust)
        language = self._detect_language(user_message)

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
            if any(kw in msg_lower for kw in ['allahindlus', 'soodustus', 'soodsamalt', 'kupong', 'kood', 'odavam', 'kallis', 'liiga kallis', 'odavamalt', 'discount', 'cheaper', 'скидка', 'дешевле', 'atlaide', 'nuolaida']):
                # Vaata vestluse ajalugu - kas TAIG10 on juba mainitud?
                # Filtreeri välja proaktiivsed sõnumid (ei loe allahindluse tasemena)
                history_text = ' '.join([m.get('content', '') for m in session['messages'][-6:] if not m.get('content', '').startswith('[PROAKTIIVNE')]).lower()
                if 'taig15' in history_text:
                    product_context += "⚡ KLIENT KAUPLEB EDASI! TAIG15 (15%) on JUBA pakutud - see ON meie PARIM pakkumine. Ütle sõbralikult aga kindlalt, et rohkem allahindlust pole võimalik. Rõhuta et 15% on VÄGA hea pakkumine! Kui nad ikka ei osta, soovita kirjutada veebipood@taig.ee hulgipakkumise jaoks.\n\n"
                elif 'taig10' in history_text:
                    product_context += "⚡ Klient tahab VEEL PAREMAT hinda! TAIG10 (10%) on juba mainitud. Nüüd tee ERIPAKKUMINE: kood TAIG15 annab 15% allahindlust! Ütle: 'Okei, teen teile eripakkumise - kood TAIG15 annab koguni 15% soodustust! See on meie absoluutselt parim hind! 🔥' Loo kiireloomulisust!\n\n"
                else:
                    product_context += "⚡ Klient küsib allahindlust! Alusta TAIG10-ga (10%). Ütle: 'Mul on teile hea pakkumine! Kasutage koodi TAIG10 ja saate 10% soodsamalt! 🎉' ÄRA maini veel TAIG15 - see on alles viimane trump!\n\n"
            elif any(kw in msg_lower for kw in ['tarne', 'kohaletoimetam', 'saatmine', 'pakiautomaat', 'kuller', 'delivery', 'shipping', 'доставка', 'piegāde', 'pristatymas']):
                product_context += "⚡ Klient küsib tarneinfot. Vasta: Venipak kuller (ukseni) ja Itella SmartPOST (pakiautomaat). TASUTA tarne alates 50€! Tarneaeg 1-7 tööpäeva. Teenindus ainult Eestis.\n\n"
            elif any(kw in msg_lower for kw in ['makse', 'makseviis', 'pangalink', 'kaardimaks', 'järelmaks', 'payment', 'оплата', 'maksājums', 'mokėjimas']):
                product_context += "⚡ Klient küsib makseviise. Vasta: Swedbank ja SEB pangalink. Äriklientidele krediidikonto. Uutele klientidele ettemaksuarve (5 päeva). Taig e-poel PUUDUB ligipääs kliendi pangaandmetele.\n\n"
            elif any(kw in msg_lower for kw in ['tagastus', 'vahetus', 'reklamatsioon', 'garantii', 'return', 'возврат', 'atgriešana', 'grąžinimas']):
                product_context += "⚡ Klient küsib tagastuse kohta. Vasta: 14 päeva tagastusõigus alates kättesaamisest. Toode kasutamata ja originaalpakendis. Tagastuskulu kuni 10€ (v.a. kui toode ei vastanud tellimusele). Raha tagastatakse 30 päeva jooksul. Saada avaldus veebipood@taig.ee.\n\n"
            elif any(kw in msg_lower for kw in ['hulgi', 'suurem tellimus', 'erikokku', 'wholesale', 'оптом', 'vairumtirdzniecība']):
                product_context += "⚡ Klient küsib hulgimüügi kohta. Vasta: 100+ ühiku puhul erikokkulepped ja krediidikonto. Kirjutage veebipood@taig.ee või helistage +372 514 2252.\n\n"

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

            # Logi koos AI vastusega
            self._log_query(session_id, user_message, language, page_context=page_context, ai_response=assistant_message)

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
