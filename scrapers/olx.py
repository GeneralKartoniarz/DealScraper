from urllib.parse import quote
import bs4
from curl_cffi import requests


def scrape_olx(
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

    formatted_query = clean_query.lower().replace(" ", "-")
    loc_slug = location.strip().lower().replace(" ", "-")
    
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
        if min_price.isdigit():
            params["search[filter_float_price:from]"] = min_price
        if max_price.isdigit():
            params["search[filter_float_price:to]"] = max_price
        if distance.isdigit() and int(distance) > 0:
            params["search[dist]"] = distance

        try:
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

                title_tag = card.find("h6") or card.find("h4") or card.find("h3")
                title = title_tag.get_text(strip=True) if title_tag else ""

                if not title or title.lower() == "brak tytułu":
                    continue

                price_tag = card.find("p", {"data-testid": "ad-price"}) or card.select_one("[data-testid='ad-price']")
                price = price_tag.get_text(strip=True) if price_tag else "Brak ceny"

                location_tag = card.find("p", {"data-testid": "location-date"}) or card.select_one("[data-testid='location-date']")
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