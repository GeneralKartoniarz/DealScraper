import re
import unicodedata
import bs4
from curl_cffi import requests


def _slugify(text: str) -> str:
    """Zamienia tekst na czysty ASCII slug URL dla OLX (np. 'Kraków' -> 'krakow', 'Łódź' -> 'lodz')."""
    if not text:
        return ""
    text = text.replace('ł', 'l').replace('Ł', 'L')
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    text = text.lower().strip()
    text = re.sub(r'[^a-z0-9]+', '-', text)
    return text.strip('-')


def _extract_olx_image_url(img_tag) -> str:
    """Wyciąga prawdziwy adres URL zdjęcia z CDN OLX (apollo.olxcdn.com), omijając zaślepki Lazy Loading (data:image)."""
    if not img_tag:
        return ""

    srcset = img_tag.get("srcset", "")
    if srcset:
        first_part = srcset.split(",")[0].strip().split()[0]
        if first_part.startswith("http") or first_part.startswith("//"):
            return "https:" + first_part if first_part.startswith("//") else first_part

    data_src = img_tag.get("data-src", "")
    if data_src and not data_src.startswith("data:"):
        return "https:" + data_src if data_src.startswith("//") else data_src

    src = img_tag.get("src", "")
    if src and not src.startswith("data:") and "no_thumbnail" not in src:
        return "https:" + src if src.startswith("//") else src

    return ""


def scrape_olx(
    query: str, 
    min_price: str = "", 
    max_price: str = "", 
    location: str = "", 
    distance: str = "0", 
    max_offers: int = 50,
    all_offers: bool = False,
    sort_by: str = "default"
) -> list[dict]:
    clean_query = query.strip()
    if not clean_query:
        return []

    formatted_query = _slugify(clean_query)
    loc_slug = _slugify(location)
    
    loc_path = f"{loc_slug}/" if loc_slug else "oferty/"
    base_url = f"https://www.olx.pl/{loc_path}q-{formatted_query}/"

    results = []
    page = 1
    max_page_safety = 30 if all_offers else (max_offers // 30) + 3

    while page <= max_page_safety:
        if not all_offers and len(results) >= max_offers:
            break

        params = {}
        if page > 1:
            params["page"] = page
        if min_price.isdigit() and int(min_price) > 0:
            params["search[filter_float_price:from]"] = min_price
        if max_price.isdigit() and int(max_price) > 0:
            params["search[filter_float_price:to]"] = max_price
        if distance.isdigit() and int(distance) > 0:
            params["search[dist]"] = distance

        if sort_by == "price_asc":
            params["search[order]"] = "filter_float_price:asc"
        elif sort_by == "price_desc":
            params["search[order]"] = "filter_float_price:desc"
        elif sort_by == "date_desc":
            params["search[order]"] = "created_at:desc"
        elif sort_by == "date_asc":
            params["search[order]"] = "created_at:asc"

        try:
            response = requests.get(
                base_url, 
                params=params, 
                impersonate="chrome", 
                timeout=12
            )

            if response.status_code == 404 and loc_slug:
                print(f"[OLX] Miejscowość '{loc_slug}' nie tworzy osobnego sluga. Przejście do wyszukiwania ogólnego...")
                base_url = f"https://www.olx.pl/oferty/q-{formatted_query}/"
                response = requests.get(
                    base_url, 
                    params=params, 
                    impersonate="chrome", 
                    timeout=12
                )

            print(f"[OLX] Strona {page} | Status HTTP: {response.status_code}")

            if response.status_code != 200:
                print(f"[OLX] Błąd HTTP {response.status_code}. Przerywam pobieranie.")
                break

            soup = bs4.BeautifulSoup(response.text, "html.parser")
            
            cards = soup.select("div[data-cy='l-card'], div[data-testid='l-card']")
            if not cards:
                offer_links = soup.select("a[href*='/d/oferta/'], a[href*='olx.pl/d/oferta/']")
                cards = []
                for link in offer_links:
                    parent = link.find_parent("div", {"data-cy": "l-card"}) or link.find_parent("div", {"data-testid": "l-card"}) or link.find_parent("div")
                    if parent and parent not in cards:
                        cards.append(parent)

            if not cards:
                print(f"[OLX] Brak kart ogłoszeń na stronie {page}.")
                break

            found_on_page = 0

            for card in cards:
                if not all_offers and len(results) >= max_offers:
                    break

                link_tag = card.find("a", href=True)
                if not link_tag:
                    continue

                href = link_tag["href"]
                link = href if href.startswith("http") else f"https://www.olx.pl{href}"

                title_tag = card.find("h6") or card.find("h4") or card.find("h3") or card.select_one("[class*='title']")
                title = title_tag.get_text(strip=True) if title_tag else ""

                if not title or title.lower() == "brak tytułu":
                    continue

                price_tag = card.find("p", {"data-testid": "ad-price"}) or card.select_one("[data-testid='ad-price']")
                price = price_tag.get_text(strip=True) if price_tag else "Brak ceny"

                location_tag = card.find("p", {"data-testid": "location-date"}) or card.select_one("[data-testid='location-date']")
                raw_location = location_tag.get_text(strip=True) if location_tag else "Brak danych"
                loc = raw_location.split(" - ")[0] if " - " in raw_location else raw_location

                img_tag = card.find("img")
                image_url = _extract_olx_image_url(img_tag)

                results.append({
                    "title": title,
                    "price": price,
                    "location": loc,
                    "source": "OLX",
                    "image_url": image_url,
                    "link": link
                })
                found_on_page += 1

            if found_on_page == 0:
                break

            page += 1

        except Exception as e:
            print(f"[OLX] Wyjątek podczas pobierania: {e}")
            break

    if not all_offers and len(results) > max_offers:
        results = results[:max_offers]

    return results