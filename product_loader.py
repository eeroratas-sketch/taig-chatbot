"""
Magento tooteandmete laadija ja cache.
Laeb GraphQL kaudu kõik tooted + rikastab EAN/laoseis andmetega stock XML-ist.
"""
import requests
import json
import os
import time
import re
import logging
from datetime import datetime, timedelta
import xml.etree.ElementTree as ET

import config

log = logging.getLogger('taig_chatbot.loader')


def _strip_html(html_str):
    """Eemalda HTML märgendid."""
    if not html_str:
        return ''
    text = re.sub(r'<[^>]+>', ' ', html_str)
    text = re.sub(r'\s+', ' ', text).strip()
    # Decode HTML entities
    text = text.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
    text = text.replace('&quot;', '"').replace('&#39;', "'")
    return text


def _fetch_products_page(page, page_size=100):
    """Laeb ühe lehekülje tooteid Magento GraphQL-ist."""
    query = """
    {
      products(
        search: ""
        pageSize: %d
        currentPage: %d
      ) {
        total_count
        items {
          sku
          name
          url_key
          price_range {
            minimum_price {
              regular_price { value }
              final_price { value }
            }
          }
          image { url }
          description { html }
          short_description { html }
          stock_status
          categories {
            name
            breadcrumbs { category_name }
          }
        }
      }
    }
    """ % (page_size, page)

    try:
        resp = requests.post(
            config.MAGENTO_GRAPHQL_URL,
            json={"query": query},
            timeout=120
        )
        data = resp.json()

        if 'errors' in data:
            log.error(f"GraphQL viga leht {page}: {data['errors'][0]['message']}")
            return [], 0

        products_data = data['data']['products']
        return products_data['items'], products_data['total_count']
    except Exception as e:
        log.error(f"GraphQL paering ebaonnestus leht {page}: {e}")
        return [], 0


def _fetch_stock_xml():
    """Laeb EAN ja laoseisu andmed stock XML-ist."""
    log.info("Laen stock XML andmeid...")
    try:
        resp = requests.get(config.STOCK_XML_URL, timeout=120)
        content = resp.content
        if content.startswith(b'\xef\xbb\xbf'):
            content = content[3:]
        root = ET.fromstring(content)

        stock_data = {}
        for prod in root.findall('product'):
            sku_el = prod.find('sku')
            ean_el = prod.find('ean')
            qty_el = prod.find('stock') or prod.find('quantity')

            if sku_el is not None and sku_el.text:
                sku = sku_el.text.strip()
                stock_data[sku] = {
                    'ean': ean_el.text.strip() if ean_el is not None and ean_el.text else '',
                    'qty': int(float(qty_el.text.strip())) if qty_el is not None and qty_el.text else 0,
                }

        log.info(f"Stock XML: {len(stock_data)} toodet")
        return stock_data
    except Exception as e:
        log.error(f"Stock XML laadimine ebaonnestus: {e}")
        return {}


def _extract_brand(name, categories):
    """Tuvasta bränd toote nimest."""
    known_brands = [
        'Thule', 'Case Logic', 'Majewski', 'St.Right', 'Erich Krause',
        'Maped', 'Milan', 'Pentel', 'Pilot', 'Staedtler', 'Faber-Castell',
        'Herlitz', 'Samsonite', 'Nike', 'Adidas', 'Puma',
    ]
    name_lower = name.lower()
    for brand in known_brands:
        if brand.lower() in name_lower:
            return brand
    return ''


def _extract_category(categories):
    """Tõmba välja põhikategooria ja alamkategooria."""
    if not categories:
        return '', ''

    main_cat = ''
    sub_cat = ''

    for cat in categories:
        name = cat.get('name', '')
        breadcrumbs = cat.get('breadcrumbs') or []

        if breadcrumbs:
            main_cat = breadcrumbs[0].get('category_name', '')
            sub_cat = name
        elif not main_cat:
            main_cat = name

    return main_cat, sub_cat


def _build_search_text(product):
    """Ehita otsingu tekst - kõik olulised sõnad ühes stringis."""
    parts = [
        product['name'],
        product['brand'],
        product['main_category'],
        product['sub_category'],
        product['short_description'][:200] if product['short_description'] else '',
    ]
    text = ' '.join(p for p in parts if p).lower()
    return text


def fetch_all_products():
    """Laeb kõik tooted Magento GraphQL-ist ja rikastab stock XML andmetega."""
    log.info("Alustan kogu kataloogi laadimist...")

    # 1. Laeme stock XML esmalt
    stock_data = _fetch_stock_xml()

    # 2. Laeme GraphQL tooted lehekülgede kaupa
    all_products = []
    page = 1
    total_count = None
    placeholder_url = 'placeholder'

    while True:
        items, total = _fetch_products_page(page, page_size=100)

        if total_count is None:
            total_count = total
            log.info(f"Kokku {total_count} toodet Magento's")

        if not items:
            break

        for item in items:
            sku = item.get('sku', '')
            name = item.get('name', '')
            url_key = item.get('url_key', '')

            # Hind
            price_range = item.get('price_range', {})
            min_price = price_range.get('minimum_price', {})
            regular_price = min_price.get('regular_price', {}).get('value', 0)
            final_price = min_price.get('final_price', {}).get('value', 0)

            # Pilt
            image_url = item.get('image', {}).get('url', '')
            has_image = bool(image_url) and placeholder_url not in image_url.lower()

            # Kirjeldused
            description = _strip_html(item.get('description', {}).get('html', ''))
            short_desc = _strip_html(item.get('short_description', {}).get('html', ''))

            # Kategooriad
            main_cat, sub_cat = _extract_category(item.get('categories', []))

            # Bränd
            brand = _extract_brand(name, item.get('categories', []))

            # Stock andmed XML-ist
            stock_info = stock_data.get(sku, {})
            ean = stock_info.get('ean', '')
            qty = stock_info.get('qty', 0)

            # Magento stock status
            stock_status = item.get('stock_status', '')
            in_stock = stock_status == 'IN_STOCK' or qty > 0

            product = {
                'sku': sku,
                'name': name,
                'url_key': url_key,
                'url': f"{config.STORE_BASE_URL}/{url_key}" if url_key else '',
                'price': final_price or regular_price,
                'regular_price': regular_price,
                'on_sale': final_price < regular_price if final_price and regular_price else False,
                'in_stock': in_stock,
                'qty': qty,
                'has_image': has_image,
                'image_url': image_url if has_image else '',
                'description': description,
                'short_description': short_desc,
                'main_category': main_cat,
                'sub_category': sub_cat,
                'brand': brand,
                'ean': ean,
            }

            # Otsingu tekst
            product['search_text'] = _build_search_text(product)

            all_products.append(product)

        log.info(f"  Laetud leht {page}: {len(items)} toodet (kokku: {len(all_products)})")
        page += 1
        time.sleep(0.3)  # Ära koorma serverit üle

        if len(all_products) >= total_count:
            break

    log.info(f"Laaditud kokku {len(all_products)} toodet")
    return all_products


def save_cache(products):
    """Salvesta tooted cache faili."""
    os.makedirs(os.path.dirname(config.CACHE_FILE), exist_ok=True)
    cache = {
        'timestamp': datetime.now().isoformat(),
        'count': len(products),
        'products': products,
    }
    with open(config.CACHE_FILE, 'w', encoding='utf-8') as f:
        json.dump(cache, f, ensure_ascii=False, indent=1)
    log.info(f"Cache salvestatud: {len(products)} toodet")


def load_cache():
    """Laadi tooted cache failist. Tagastab (products, is_fresh)."""
    if not os.path.exists(config.CACHE_FILE):
        return None, False

    try:
        with open(config.CACHE_FILE, 'r', encoding='utf-8') as f:
            cache = json.load(f)

        timestamp = datetime.fromisoformat(cache['timestamp'])
        age = datetime.now() - timestamp
        is_fresh = age < timedelta(hours=config.CACHE_TTL_HOURS)

        products = cache['products']
        log.info(f"Cache laetud: {len(products)} toodet, vanus: {age}")
        return products, is_fresh
    except Exception as e:
        log.error(f"Cache lugemine ebaonnestus: {e}")
        return None, False


def get_products(force_refresh=False):
    """Hangi tooted - cache'ist või Magento'st."""
    if not force_refresh:
        products, is_fresh = load_cache()
        if products and is_fresh:
            return products
        if products:
            log.info("Cache on vananenud, uuendan taustal...")

    products = fetch_all_products()
    if products:
        save_cache(products)
    return products


if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(name)s %(levelname)s: %(message)s')
    products = get_products(force_refresh=True)
    print(f"\nKokku: {len(products)} toodet")

    # Statistika
    with_image = sum(1 for p in products if p['has_image'])
    in_stock = sum(1 for p in products if p['in_stock'])
    with_brand = sum(1 for p in products if p['brand'])
    print(f"Pildiga: {with_image}")
    print(f"Laos: {in_stock}")
    print(f"Brandiga: {with_brand}")

    # Top brändid
    from collections import Counter
    brands = Counter(p['brand'] for p in products if p['brand'])
    print(f"\nTop braendid:")
    for brand, count in brands.most_common(10):
        print(f"  {brand}: {count}")
