"""
Tooteotsi mootor - kiire märksõnapõhine otsing üle cached toodete.
"""
import re
import logging

log = logging.getLogger('taig_chatbot.search')

# Eesti stoppsõnad - filtreerida otsingust välja
STOP_WORDS = {
    'ja', 'või', 'on', 'ei', 'see', 'mis', 'kas', 'kui', 'et',
    'ma', 'sa', 'ta', 'me', 'te', 'nad', 'oma', 'seda', 'selle',
    'minu', 'sinu', 'tema', 'meie', 'teie', 'nende',
    'ka', 'veel', 'juba', 'siis', 'nii', 'seal', 'siin',
    'kus', 'kuhu', 'kust', 'millal', 'kuidas', 'miks',
    'üks', 'kaks', 'kolm', 'palju', 'vähe',
    'aga', 'kuid', 'sest', 'ning',
    'the', 'and', 'or', 'for', 'with', 'from', 'this', 'that',
    'mida', 'millist', 'soovita', 'otsin', 'tahan', 'vajan',
    'soovin', 'osta', 'ostan', 'osta', 'ostma', 'palun',
    'mulle', 'endale', 'lapsele', 'kooli', 'kontorisse',
    'head', 'parimat', 'sobivat', 'odavat', 'soodsat',
    'soovitan', 'näita', 'näidata', 'leia', 'otsi',
    # Vene stop-sõnad
    'вас', 'есть', 'ли', 'мне', 'для', 'что', 'как', 'это', 'где', 'нет',
    'хочу', 'купить', 'нужно', 'нужна', 'нужны', 'можно', 'пожалуйста',
    # Soome stop-sõnad
    'onko', 'teillä', 'minulle', 'haluan', 'ostaa', 'tarvitsen',
    # Läti stop-sõnad
    'vai', 'ir', 'man', 'jums', 'kur', 'kas', 'ko', 'kā', 'nav', 'gribu', 'pirkt', 'lūdzu', 'vajag',
    # Leedu stop-sõnad
    'ar', 'yra', 'man', 'jums', 'kur', 'kas', 'ką', 'kaip', 'nėra', 'noriu', 'pirkti', 'prašau', 'reikia',
    # Inglise stop-sõnad (laiendatud)
    'have', 'you', 'your', 'any', 'some', 'looking', 'need', 'want', 'buy',
    'can', 'could', 'please', 'show', 'find', 'search', 'get', 'like',
}

# Sünonüümid eesti-inglise segakeelele
SYNONYMS = {
    'kohver': ['kohver', 'kohvrid', 'kohvrit', 'suitcase', 'luggage', 'carry-on'],
    'seljakott': ['seljakott', 'seljakotid', 'seljakoti', 'backpack', 'rucksack'],
    'kott': ['kott', 'kotid', 'koti', 'bag', 'bags'],
    'matkakott': ['matkakott', 'matkakotid', 'hiking', 'trekking', 'matkaseljakott'],
    'koolikott': ['koolikott', 'koolikotid', 'school bag', 'schoolbag'],
    'sülearvutikott': ['sülearvuti', 'laptop', 'notebook', 'arvutikott'],
    'reisikohver': ['reisikohver', 'reisikohvrid', 'travel', 'luggage'],
    'pastakas': ['pastakas', 'pastakad', 'pen', 'pens', 'kirjutusvahend'],
    'pliiats': ['pliiats', 'pliiatsid', 'pencil', 'pencils'],
    'kalkulaator': ['kalkulaator', 'kalkulaatorid', 'calculator'],
    'käärid': ['käärid', 'scissors'],
    'marker': ['marker', 'markerid', 'highlighter'],
    'kustukumm': ['kustukumm', 'kustutuskumm', 'eraser'],
    'kaustik': ['kaustik', 'kaustikud', 'vihik', 'notebook'],
    'mapid': ['mapp', 'mapid', 'kaust', 'folder'],
    'pinal': ['pinal', 'pinalid', 'pencil case'],
    'joogivesi': ['joogipudel', 'pudel', 'bottle', 'water'],
    'koolitarbed': ['koolitarbed', 'koolitarbeid', 'koolikaubad', 'koolikaupu', 'kooliasjad',
                    'koolitarve', 'koolitarvete', 'school supplies'],
    'koolikaubad': ['koolikaubad', 'koolitarbed', 'koolitarbeid', 'koolikaupu', 'kooliasjad',
                    'kooliasjadega', 'school supplies'],
    'kontoritarbed': ['kontoritarbed', 'kontoritarbeid', 'kontorikaubad', 'kontorikaupu',
                      'kontoriasjad', 'kontoritarvete', 'bürootarbed', 'office supplies'],
    'kirjutusvahend': ['kirjutusvahend', 'kirjutusvahendid', 'kirjutusvahendeid', 'writing'],
    'teritaja': ['teritaja', 'teritajad', 'teritajat', 'sharpener'],
    'joonlaud': ['joonlaud', 'joonlauad', 'ruler'],
    'liim': ['liim', 'liimipulk', 'liimipulgad', 'glue'],
    'kleeplint': ['kleeplint', 'teip', 'tape', 'scotch'],
    'värv': ['värv', 'värvid', 'värve', 'paint', 'guašš', 'akvarellid', 'akvarellvärv'],
    'pintsel': ['pintsel', 'pintslid', 'brush'],
    'viltpliiats': ['viltpliiats', 'viltpliiatsid', 'vildikas', 'vildikad', 'felt pen', 'marker'],
    'klammerdaja': ['klammerdaja', 'klamber', 'klambrid', 'stapler'],
    'augustaja': ['augustaja', 'auguraud', 'punch', 'hole punch'],
    'thule': ['thule'],
    'case logic': ['case', 'logic', 'caselogic'],
    # Vene keele sünonüümid
    'ручка': ['ручка', 'ручки', 'pastakas', 'pastakad', 'pen'],
    'карандаш': ['карандаш', 'карандаши', 'pliiats', 'pliiatsid', 'pencil'],
    'ножницы': ['ножницы', 'käärid', 'scissors'],
    'клей': ['клей', 'liim', 'liimipulk', 'glue'],
    'ластик': ['ластик', 'резинка', 'kustukumm', 'eraser'],
    'пенал': ['пенал', 'pinal', 'pencil case'],
    'тетрадь': ['тетрадь', 'тетради', 'vihik', 'kaustik', 'notebook'],
    'краски': ['краски', 'гуашь', 'акварель', 'värv', 'värvid', 'guašš', 'akvarellid'],
    'кисть': ['кисть', 'кисточка', 'pintsel', 'brush'],
    'линейка': ['линейка', 'joonlaud', 'ruler'],
    'маркер': ['маркер', 'маркеры', 'marker', 'markerid', 'highlighter'],
    'рюкзак': ['рюкзак', 'seljakott', 'backpack'],
    'чемодан': ['чемодан', 'kohver', 'suitcase', 'luggage'],
    'школьные': ['школьные', 'школьных', 'принадлежности', 'koolitarbed', 'koolikaubad', 'school supplies'],
    'канцтовары': ['канцтовары', 'канцелярия', 'kontoritarbed', 'office supplies'],
    # Soome keele sünonüümid
    'kynä': ['kynä', 'kynät', 'pastakas', 'pen'],
    'lyijykynä': ['lyijykynä', 'pliiats', 'pencil'],
    'sakset': ['sakset', 'käärid', 'scissors'],
    'liima': ['liima', 'liim', 'glue'],
    'reppu': ['reppu', 'seljakott', 'backpack'],
    'matkalaukku': ['matkalaukku', 'kohver', 'suitcase'],
    'koulutarvikkeet': ['koulutarvikkeet', 'koolitarbed', 'school supplies'],
    # Läti keele sünonüümid
    'pildspalva': ['pildspalva', 'pildspalvas', 'pastakas', 'pen'],
    'zīmulis': ['zīmulis', 'zīmuļi', 'pliiats', 'pencil'],
    'šķēres': ['šķēres', 'käärid', 'scissors'],
    'līme': ['līme', 'līmes', 'liim', 'glue'],
    'dzēšgumija': ['dzēšgumija', 'kustukumm', 'eraser'],
    'penālis': ['penālis', 'pinal', 'pencil case'],
    'burtnīca': ['burtnīca', 'burtnīcas', 'vihik', 'notebook'],
    'krāsas': ['krāsas', 'guaša', 'akvarele', 'värv', 'guašš', 'paint'],
    'ota': ['ota', 'otas', 'pintsel', 'brush'],
    'lineāls': ['lineāls', 'joonlaud', 'ruler'],
    'marķieris': ['marķieris', 'marker', 'highlighter'],
    'mugursoma': ['mugursoma', 'seljakott', 'backpack'],
    'koferis': ['koferis', 'kohver', 'suitcase'],
    'skolas': ['skolas', 'piederumi', 'koolitarbed', 'koolikaubad', 'school supplies'],
    'kancelejas': ['kancelejas', 'preces', 'kontoritarbed', 'office supplies'],
    # Leedu keele sünonüümid
    'rašiklis': ['rašiklis', 'rašikliai', 'pastakas', 'pen'],
    'pieštukas': ['pieštukas', 'pieštukai', 'pliiats', 'pencil'],
    'žirklės': ['žirklės', 'käärid', 'scissors'],
    'klijai': ['klijai', 'liim', 'glue'],
    'trintukas': ['trintukas', 'kustukumm', 'eraser'],
    'penalas': ['penalas', 'pinal', 'pencil case'],
    'sąsiuvinis': ['sąsiuvinis', 'sąsiuviniai', 'vihik', 'notebook'],
    'dažai': ['dažai', 'guašas', 'akvarelė', 'värv', 'guašš', 'paint'],
    'teptukas': ['teptukas', 'pintsel', 'brush'],
    'liniuotė': ['liniuotė', 'joonlaud', 'ruler'],
    'žymeklis': ['žymeklis', 'marker', 'highlighter'],
    'kuprinė': ['kuprinė', 'seljakott', 'backpack'],
    'lagaminas': ['lagaminas', 'kohver', 'suitcase'],
    'mokyklinės': ['mokyklinės', 'priemonės', 'mokykliniai', 'koolitarbed', 'koolikaubad', 'school supplies'],
    'kanceliarinės': ['kanceliarinės', 'prekės', 'kontoritarbed', 'office supplies'],
}


def tokenize(text):
    """Tükelda tekst sõnadeks, eemalda stoppsõnad."""
    words = re.findall(r'[a-züõäöšžа-яёА-ЯЁäöåéèêëïîôûüùçāčēģīķļņšūžąčęėįšųūž\d]+', text.lower())
    return [w for w in words if w not in STOP_WORDS and len(w) > 1]


def _expand_query(tokens):
    """Lisa sünonüümid päringule."""
    expanded = set(tokens)
    for token in tokens:
        for key, syns in SYNONYMS.items():
            if token in syns or token == key:
                expanded.update(syns)
                expanded.add(key)
    return list(expanded)


def _extract_price_range(query):
    """Tuvasta hinnavahemik päringust."""
    min_price = None
    max_price = None

    # "alla 50€" / "alla 50 eurot" / "kuni 50€"
    m = re.search(r'(?:alla|kuni|max|maksimaalselt)\s*(\d+)', query.lower())
    if m:
        max_price = float(m.group(1))

    # "üle 20€" / "alates 20€" / "vähemalt 20"
    m = re.search(r'(?:üle|alates|vähemalt|min|minimaalselt)\s*(\d+)', query.lower())
    if m:
        min_price = float(m.group(1))

    # "50-100€" / "50 kuni 100"
    m = re.search(r'(\d+)\s*[-–]\s*(\d+)', query)
    if m:
        min_price = float(m.group(1))
        max_price = float(m.group(2))

    return min_price, max_price


class ProductSearch:
    def __init__(self, products):
        self.products = products
        self.index = {}  # word -> [(product_idx, weight)]
        self._build_index()

    def _build_index(self):
        """Ehita pöördindeks."""
        log.info(f"Ehitan otsinguindeksit {len(self.products)} tootele...")

        for idx, product in enumerate(self.products):
            # Nimi - kaal 4
            for word in tokenize(product['name']):
                self.index.setdefault(word, []).append((idx, 4))

            # Bränd - kaal 5
            if product['brand']:
                for word in tokenize(product['brand']):
                    self.index.setdefault(word, []).append((idx, 5))

            # Kategooria - kaal 3
            for word in tokenize(product['main_category'] + ' ' + product['sub_category']):
                self.index.setdefault(word, []).append((idx, 3))

            # Lühikirjeldus - kaal 1
            if product['short_description']:
                for word in tokenize(product['short_description'][:300]):
                    self.index.setdefault(word, []).append((idx, 1))

            # SKU - kaal 6 (täpne otsing)
            self.index.setdefault(product['sku'].lower(), []).append((idx, 6))

        log.info(f"Indeks valmis: {len(self.index)} unikaalset sona")

    def search(self, query, max_results=8, only_in_stock=False):
        """Otsi tooteid päringu järgi."""
        tokens = tokenize(query)
        if not tokens:
            return []

        # Laienda sünonüümidega
        expanded = _expand_query(tokens)

        # Hinnafilter
        min_price, max_price = _extract_price_range(query)

        # Skoorima
        scores = {}
        for token in expanded:
            # Täpne vaste
            if token in self.index:
                for product_idx, weight in self.index[token]:
                    actual_weight = weight if token in tokens else weight * 0.5
                    scores[product_idx] = scores.get(product_idx, 0) + actual_weight

        # Tüve-otsing originaaltokenitele, mis ei andnud tulemust
        if not scores and len(tokens) > 0:
            for token in tokens:
                stem = token[:5] if len(token) >= 5 else token
                for word, entries in self.index.items():
                    if word.startswith(stem) or stem.startswith(word[:5] if len(word) >= 5 else word):
                        for product_idx, weight in entries:
                            scores[product_idx] = scores.get(product_idx, 0) + weight * 0.3

        # Boonused
        for idx, score in list(scores.items()):
            product = self.products[idx]

            # Laos olev toode saab boonust
            if product['in_stock']:
                scores[idx] += 2

            # Pildiga toode saab boonust
            if product['has_image']:
                scores[idx] += 1

            # Hinnafilter
            if min_price and product['price'] < min_price:
                scores[idx] *= 0.1
            if max_price and product['price'] > max_price:
                scores[idx] *= 0.1

            # Laos filter
            if only_in_stock and not product['in_stock']:
                del scores[idx]
                continue

        # Sorteeri skoori järgi
        sorted_results = sorted(scores.items(), key=lambda x: -x[1])

        results = []
        for idx, score in sorted_results[:max_results]:
            product = self.products[idx].copy()
            product['_score'] = score
            results.append(product)

        return results

    def get_by_sku(self, sku):
        """Leia toode SKU järgi."""
        for p in self.products:
            if p['sku'] == sku:
                return p
        return None

    def get_by_category(self, category, max_results=10):
        """Leia tooted kategooria järgi."""
        results = []
        cat_lower = category.lower()
        for p in self.products:
            if (cat_lower in p['main_category'].lower() or
                cat_lower in p['sub_category'].lower()):
                results.append(p)
        # Sorteeri: laos olevad enne, siis hinna järgi
        results.sort(key=lambda p: (not p['in_stock'], p['price']))
        return results[:max_results]

    def get_by_brand(self, brand, max_results=20):
        """Leia tooted brändi järgi."""
        results = []
        brand_lower = brand.lower()
        for p in self.products:
            if brand_lower in p['brand'].lower() or brand_lower in p['name'].lower():
                results.append(p)
        results.sort(key=lambda p: (not p['in_stock'], -p['price']))
        return results[:max_results]

    def get_stats(self):
        """Tagasta kataloogi statistika."""
        total = len(self.products)
        in_stock = sum(1 for p in self.products if p['in_stock'])
        with_image = sum(1 for p in self.products if p['has_image'])
        brands = {}
        for p in self.products:
            if p['brand']:
                brands[p['brand']] = brands.get(p['brand'], 0) + 1
        categories = {}
        for p in self.products:
            cat = p['main_category'] or 'Muu'
            categories[cat] = categories.get(cat, 0) + 1

        return {
            'total': total,
            'in_stock': in_stock,
            'with_image': with_image,
            'top_brands': sorted(brands.items(), key=lambda x: -x[1])[:10],
            'top_categories': sorted(categories.items(), key=lambda x: -x[1])[:10],
        }
