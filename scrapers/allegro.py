import re
import time
from urllib.parse import quote
import bs4
from curl_cffi import requests


def _clean_price_string(raw_text: str) -> str:
    if not raw_text:
        return "Brak ceny"

    text = raw_text
    text = re.sub(r'-\d+%', '', text)
    text = re.sub(r'Kup\s*teraz', '', text, flags=re.IGNORECASE)
    text = re.sub(r'do\s*negocjacji', '', text, flags=re.IGNORECASE)
    text = re.sub(r'licytacja', '', text, flags=re.IGNORECASE)

    matches = re.findall(r'(\d[\d\s,.]*)\s*(?:zł|PLN)', text, re.IGNORECASE)

    if matches:
        last_price = matches[-1].strip()
        last_price = re.sub(r'\s+', ' ', last_price)
        return f"{last_price} zł"

    return "Brak ceny"


def scrape_allegro(
    query: str, 
    min_price: str = "", 
    max_price: str = "", 
    location: str = "", 
    distance: str = "0", 
    max_offers: int = 50,
    all_offers: bool = False
) -> list[dict]:
    clean_query = query.strip()
    if not clean_query:
        return []

    encoded_query = quote(clean_query)
    base_url = f"https://allegrolokalnie.pl/oferty/q/{encoded_query}"

    session = requests.Session()
    
    # 1. Rozgrzewanie sesji (pobranie ciasteczek ze strony głównej)
    try:
        session.get("https://allegrolokalnie.pl/", impersonate="chrome", timeout=8)
        time.sleep(0.5)
    except Exception:
        pass

    results = []
    page = 1
    max_page_safety = 30 if all_offers else (max_offers // 20) + 3

    while page <= max_page_safety:
        if not all_offers and len(results) >= max_offers:
            break

        params = {}
        if page > 1:
            params["p"] = page
            time.sleep(0.5)
        if min_price.isdigit():
            params["price_from"] = min_price
        if max_price.isdigit():
            params["price_to"] = max_price
        if location.strip():
            params["city"] = location

        try:
            response = session.get(
                base_url, 
                params=params, 
                impersonate="chrome", 
                timeout=12
            )

            # W przypadku 429 czekamy 3 sekundy i ponawiamy próbę
            if response.status_code == 429:
                print(f"[Allegro] Otrzymano status 429 na stronie {page}. Czekam 3.0s...")
                time.sleep(3.0)
                response = session.get(
                    base_url, 
                    params=params, 
                    impersonate="chrome", 
                    timeout=12
                )

            print(f"[Allegro] Strona {page} | Status HTTP: {response.status_code}")

            if response.status_code != 200:
                print(f"[Allegro] Błąd HTTP {response.status_code}. Przerywam pobieranie.")
                break

            soup = bs4.BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("article")

            if not cards:
                cards = soup.select("article.ml-offer-card, div.lc-offer-card, div[class*='offer-card']")

            if not cards:
                print(f"[Allegro] Brak kart na stronie {page}.")
                break

            found_on_page = 0

            for card in cards:
                if not all_offers and len(results) >= max_offers:
                    break

                link_tag = card.find("a", href=True)
                if not link_tag:
                    continue

                href = link_tag["href"]
                link = href if href.startswith("http") else f"https://allegrolokalnie.pl{href}"

                title_tag = card.select_one(".ml-offer-card__title, .lc-offer-card__title, h2, h3, [class*='title']")
                title = title_tag.get_text(strip=True) if title_tag else ""

                if not title or len(title) < 2 or "Allegro Lokalnie" in title:
                    continue

                price_tag = card.select_one(
                    ".ml-offer-card__price, .lc-offer-card__price, "
                    "[class*='price'], [data-testid*='price']"
                )

                if price_tag:
                    price_copy = bs4.BeautifulSoup(str(price_tag), "html.parser")
                    for unwanted in price_copy.select("del, s, [class*='old'], [class*='crossed']"):
                        unwanted.decompose()
                    price = _clean_price_string(price_copy.get_text(separator=" ", strip=True))
                else:
                    price = _clean_price_string(card.get_text(separator=" "))

                loc_tag = card.select_one(".ml-offer-card__location, .lc-offer-card__location, [class*='location']")
                loc = loc_tag.get_text(strip=True) if loc_tag else (location.capitalize() if location else "Polska")

                img_tag = card.find("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("data-src") or img_tag.get("srcset") or ""
                    if "," in image_url:
                        image_url = image_url.split(",")[0].split()[0]
                    if image_url.startswith("//"):
                        image_url = "https:" + image_url

                results.append({
                    "title": title,
                    "price": price,
                    "location": loc,
                    "source": "ALLEGRO",
                    "image_url": image_url,
                    "link": link
                })
                found_on_page += 1

            if found_on_page == 0:
                break

            page += 1

        except Exception as e:
            print(f"[Allegro] Wyjątek podczas pobierania: {e}")
            break

    if not all_offers and len(results) > max_offers:
        results = results[:max_offers]

    return results