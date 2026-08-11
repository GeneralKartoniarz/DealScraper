from urllib.parse import quote
import bs4
import requests


def scrape_ebay(
    query: str, 
    min_price: str = "", 
    max_price: str = "", 
    location: str = "", 
    distance: str = "0", 
    max_offers: int = 50,
    all_offers: bool = False
) -> list[dict]:
    """Pobiera oferty z serwisu eBay z uwzględnieniem filtrów cenowych oraz limitu."""
    encoded_query = quote(query.strip())
    base_url = f"https://www.ebay.pl/sch/i.html?_nkw={encoded_query}"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
            "(KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        ),
        "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
    }

    results = []
    page = 1
    max_page_safety = 30 if all_offers else (max_offers // 50) + 3

    while page <= max_page_safety:
        if not all_offers and len(results) >= max_offers:
            break

        params = {
            "_pgn": page,
            "_ipg": 60,  
        }

        if min_price.isdigit():
            params["_udlo"] = min_price
        if max_price.isdigit():
            params["_udhi"] = max_price

        try:
            response = requests.get(base_url, headers=headers, params=params, timeout=10)
            if response.status_code != 200:
                break

            soup = bs4.BeautifulSoup(response.text, "html.parser")
            cards = soup.select("li.s-item")

            if not cards:
                break

            found_on_page = 0

            for card in cards:
                if not all_offers and len(results) >= max_offers:
                    break

                title_tag = card.select_one(".s-item__title")
                if not title_tag:
                    continue

                title = title_tag.get_text(strip=True)
                if not title or "Shop on eBay" in title or "Otwórz ofertę" in title:
                    continue

                link_tag = card.select_one("a.s-item__link")
                if not link_tag or not link_tag.get("href"):
                    continue
                link = link_tag["href"].split("?")[0]

                price_tag = card.select_one(".s-item__price")
                price = price_tag.get_text(strip=True) if price_tag else "Brak ceny"

                loc_tag = card.select_one(".s-item__location") or card.select_one(".s-item__item-location")
                loc = loc_tag.get_text(strip=True) if loc_tag else "Międzynarodowa"
                if loc.lower().startswith("z: "):
                    loc = loc[3:]

                img_tag = card.select_one(".s-item__image-img") or card.select_one("img")
                image_url = ""
                if img_tag:
                    image_url = img_tag.get("src") or img_tag.get("data-src") or ""

                results.append({
                    "title": title,
                    "price": price,
                    "location": loc,
                    "source": "eBY",
                    "image_url": image_url,
                    "link": link
                })
                found_on_page += 1

            if found_on_page == 0:
                break

            page += 1

        except Exception as e:
            print(f"[eBay] Błąd podczas pobierania strony {page}: {e}")
            break

    if not all_offers and len(results) > max_offers:
        results = results[:max_offers]

    return results