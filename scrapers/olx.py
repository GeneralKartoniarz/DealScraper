import unicodedata
from urllib.parse import quote
import bs4
import requests


def _slugify(text: str) -> str:
    """Zamienia nazwę miasta na wersję URL (np. Kraków -> krakow)."""
    text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
    return text.lower().strip().replace(' ', '-')


def scrape_olx(
    query: str, 
    min_price: str = "", 
    max_price: str = "", 
    location: str = "", 
    distance: str = "0", 
    max_offers: int = 50,
    all_offers: bool = False
) -> list[dict]:
    """Pobiera oferty z OLX z uwzględnieniem filtrów i dokładnego limitu ofert."""
    encoded_query = quote(query.strip())
    
    loc_path = f"{_slugify(location)}/" if location.strip() else "oferty/"
    base_url = f"https://www.olx.pl/{loc_path}q-{encoded_query}/"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pl-PL,pl;q=0.9",
    }

    results = []
    page = 1
    
    max_page_safety = 50 if all_offers else (max_offers // 40) + 3

    while page <= max_page_safety:
        if not all_offers and len(results) >= max_offers:
            break

        params = {}
        if page > 1:
            params["page"] = page
        if min_price.isdigit():
            params["search[filter_float_price:from]"] = min_price
        if max_price.isdigit():
            params["search[filter_float_price:to]"] = max_price
        if distance.isdigit() and int(distance) > 0:
            params["search[dist]"] = distance

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                break

            soup = bs4.BeautifulSoup(response.text, "html.parser")
            cards = soup.find_all("div", {"data-cy": "l-card"})

            if not cards:
                break 

            for card in cards:
                if not all_offers and len(results) >= max_offers:
                    break

                link_tag = card.find("a", href=True)
                if not link_tag:
                    continue

                href = link_tag["href"]
                link = href if href.startswith("http") else f"https://www.olx.pl{href}"

                title_tag = card.find("h6") or card.find("h4") or card.find("h3")
                title = title_tag.get_text(strip=True) if title_tag else "Brak tytułu"

                if not title or title == "Brak tytułu":
                    continue

                price_tag = card.find("p", {"data-testid": "ad-price"})
                price = price_tag.get_text(strip=True) if price_tag else "Brak ceny"

                location_tag = card.find("p", {"data-testid": "location-date"})
                raw_location = location_tag.get_text(strip=True) if location_tag else "Brak danych"
                loc = raw_location.split(" - ")[0] if " - " in raw_location else raw_location

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
                    "source": "OLX",
                    "image_url": image_url,
                    "link": link
                })

            page += 1

        except Exception as e:
            print(f"[OLX] Błąd pobierania strony {page}: {e}")
            break

    if not all_offers and len(results) > max_offers:
        results = results[:max_offers]

    return results