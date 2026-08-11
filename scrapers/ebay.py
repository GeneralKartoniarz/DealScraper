import re
import bs4
from curl_cffi import requests


def scrape_ebay(
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

    results = []

    # Lista domen eBaya do ewentualnego fallbacku
    domains = [
        ("https://www.ebay.pl/sch/i.html", "https://www.ebay.pl/"),
        ("https://www.ebay.com/sch/i.html", "https://www.ebay.com/")
    ]

    for base_url, homepage_url in domains:
        page = 1
        max_page_safety = 30 if all_offers else (max_offers // 30) + 3

        # Tworzymy spójną sesję curl_cffi z impersonacją Google Chrome 124
        session = requests.Session(impersonate="chrome124")

        # 1. Rozgrzewamy sesję (pobieramy ciasteczka Akamai ze strony głównej)
        try:
            session.get(homepage_url, timeout=8)
        except Exception as e:
            print(f"[eBay] Uwaga: Błąd rozgrzewania sesji na {homepage_url}: {e}")

        while page <= max_page_safety:
            if not all_offers and len(results) >= max_offers:
                break

            params = {"_nkw": clean_query}
            if page > 1:
                params["_pgn"] = page

            if min_price.isdigit():
                params["_udlo"] = min_price
            if max_price.isdigit():
                params["_udhi"] = max_price

            headers = {
                "Accept-Language": "pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7",
                "Referer": homepage_url,
            }

            try:
                response = session.get(base_url, params=params, headers=headers, timeout=10)
                print(f"[eBay] {base_url} Strona {page} | Status HTTP: {response.status_code}")

                if response.status_code != 200:
                    print(f"[eBay] Status {response.status_code} na {base_url}. Przechodzę do kolejnej domeny.")
                    break

                soup = bs4.BeautifulSoup(response.text, "html.parser")
                cards = soup.select("li.s-item, li[class*='s-item'], li.s-card")

                if not cards:
                    print(f"[eBay] Brak kart s-item na stronie {page}.")
                    break

                found_on_page = 0

                for card in cards:
                    if not all_offers and len(results) >= max_offers:
                        break

                    # 1. Tytuł
                    title_tag = card.select_one(".s-item__title, .s-card__title, [class*='title']")
                    if not title_tag:
                        continue

                    title_soup = bs4.BeautifulSoup(str(title_tag), "html.parser")
                    for hidden in title_soup.select(".visually-hidden, .clipped, span[class*='hidden']"):
                        hidden.decompose()

                    title = title_soup.get_text(strip=True)

                    if not title or title.lower() in ["shop on ebay", "wyniki wyszukiwania", "otwórz ofertę"] or len(title) < 2:
                        continue

                    # 2. Link
                    link_tag = card.select_one("a.s-item__link, a.su-link") or card.find("a", href=True)
                    if not link_tag or not link_tag.get("href"):
                        continue

                    raw_href = link_tag["href"]
                    if raw_href.startswith("/"):
                        link = "https://www.ebay.pl" + raw_href
                    else:
                        link = raw_href.split("?")[0]

                    # 3. Cena
                    price = "Brak ceny"
                    price_tag = card.select_one(".s-item__price, [class*='price']")
                    if price_tag:
                        raw_price = price_tag.get_text(strip=True)
                        if raw_price:
                            price = raw_price

                    if price == "Brak ceny":
                        card_text = card.get_text(separator=" ")
                        match = re.search(r'(\d+[\d\s,.]*\s*(?:zł|PLN|\$|EUR|GBP))', card_text)
                        if match:
                            price = match.group(1).strip()

                    # 4. Lokalizacja
                    loc_tag = card.select_one(".s-item__location, .s-item__item-location, .s-card__attribute-row")
                    loc = loc_tag.get_text(strip=True) if loc_tag else "Międzynarodowa"
                    if loc.lower().startswith("z: "):
                        loc = loc[3:]

                    # 5. Zdjęcie
                    img_tag = card.select_one(".s-item__image-img, img")
                    image_url = ""
                    if img_tag:
                        image_url = img_tag.get("src") or img_tag.get("data-src") or ""

                    results.append({
                        "title": title,
                        "price": price,
                        "location": loc,
                        "source": "EBAY",
                        "image_url": image_url,
                        "link": link
                    })
                    found_on_page += 1

                if found_on_page == 0:
                    break

                page += 1

            except Exception as e:
                print(f"[eBay] Wyjątek podczas pobierania: {e}")
                break

        # Jeśli pobraliśmy oferty z pierwszej domeny, przerywamy pętlę domen
        if len(results) > 0:
            break

    if not all_offers and len(results) > max_offers:
        results = results[:max_offers]

    return results