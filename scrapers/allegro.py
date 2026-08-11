from urllib.parse import quote
import bs4
import requests


def scrape_allegro(
    query: str, 
    min_price: str = "", 
    max_price: str = "", 
    location: str = "", 
    distance: str = "0", 
    max_offers: int = 50,
    all_offers: bool = False
) -> list[dict]:
    """Pobiera oferty z serwisu Allegro / Allegro Lokalnie z uwzględnieniem filtrów oraz limitu."""
    encoded_query = quote(query.strip())
    base_url = f"https://allegrolokalnie.pl/oferty/q/{encoded_query}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    results = []
    page = 1
    max_page_safety = 30 if all_offers else (max_offers // 30) + 3

    while page <= max_page_safety:
        if not all_offers and len(results) >= max_offers:
            break

        params = {}
        if page > 1:
            params["p"] = page
        if min_price.isdigit():
            params["price_from"] = min_price
        if max_price.isdigit():
            params["price_to"] = max_price
        if location.strip():
            params["city"] = location

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                break

            soup = bs4.BeautifulSoup(response.text, "html.parser")
            cards = soup.select("article.ml-offer-card, div.lc-offer-card")

            if not cards:
                cards = soup.find_all("article")

            found_on_page = 0

            for card in cards:
                if not all_offers and len(results) >= max_offers:
                    break

                # Link do ogłoszenia
                link_tag = card.find("a", href=True)
                if not link_tag:
                    continue

                href = link_tag["href"]
                link = href if href.startswith("http") else f"https://allegrolokalnie.pl{href}"

                # Tytuł
                title_tag = card.select_one(".ml-offer-card__title, .lc-offer-card__title, h2, h3")
                title = title_tag.get_text(strip=True) if title_tag else ""

                if not title or len(title) < 3:
                    continue

                # Cena
                price_tag = card.select_one(".ml-offer-card__price, .lc-offer-card__price, span.ml-offer-card__price-value")
                price = price_tag.get_text(strip=True) if price_tag else "Brak ceny"

                # Lokalizacja
                loc_tag = card.select_one(".ml-offer-card__location, .lc-offer-card__location")
                loc = loc_tag.get_text(strip=True) if loc_tag else (location.capitalize() if location else "Polska")

                # Zdjęcie
                img_tag = card.find("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("data-src") or ""
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
            print(f"[Allegro] Błąd podczas pobierania strony {page}: {e}")
            break

    if not all_offers and len(results) > max_offers:
        results = results[:max_offers]

    return results