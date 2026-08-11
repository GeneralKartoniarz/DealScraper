import re
import time
from gui import ScraperGUI
from scrapers.olx import scrape_olx
from scrapers.ebay import scrape_ebay
from scrapers.allegro import scrape_allegro


def parse_numeric_price(price_str: str, default_val: float) -> float:
    """Konwertuje dowolną cenę tekstową (np. '1 850 zł', '$45.00') na wartość numeryczną float."""
    if not price_str or "brak" in price_str.lower():
        return default_val
    cleaned = price_str.replace(" ", "").replace("\xa0", "").replace(",", ".")
    match = re.search(r'(\d+(?:\.\d+)?)', cleaned)
    if match:
        try:
            return float(match.group(1))
        except ValueError:
            pass
    return default_val


def fetch_all_offers(filters: dict) -> list[dict]:
    query = filters.get("query", "").strip()
    sort_by = filters.get("sort_by", "default")

    print("\n" + "="*50)
    print(f"[MAIN] WYSZUKIWANIE DLA FRAZY: '{query}' | SORTOWANIE: {sort_by}")
    print("="*50)

    all_results = []

    # 1. OLX
    try:
        olx_results = scrape_olx(
            query=query,
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            location=filters["location"],
            distance=filters["distance"],
            max_offers=filters["max_offers"],
            all_offers=filters["all_offers"],
            sort_by=sort_by
        )
        print(f"[MAIN] OLX -> Pobrano: {len(olx_results)} ofert.")
        all_results.extend(olx_results)
    except Exception as e:
        print(f"[MAIN] Błąd wykonania scrapera OLX: {e}")

    time.sleep(0.5)

    # 2. Allegro
    try:
        allegro_results = scrape_allegro(
            query=query,
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            location=filters["location"],
            distance=filters["distance"],
            max_offers=filters["max_offers"],
            all_offers=filters["all_offers"],
            sort_by=sort_by
        )
        print(f"[MAIN] Allegro -> Pobrano: {len(allegro_results)} ofert.")
        all_results.extend(allegro_results)
    except Exception as e:
        print(f"[MAIN] Błąd wykonania scrapera Allegro: {e}")

    time.sleep(0.5)

    # 3. eBay
    try:
        ebay_results = scrape_ebay(
            query=query,
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            location=filters["location"],
            distance=filters["distance"],
            max_offers=filters["max_offers"],
            all_offers=filters["all_offers"],
            sort_by=sort_by
        )
        print(f"[MAIN] eBay -> Pobrano: {len(ebay_results)} ofert.")
        all_results.extend(ebay_results)
    except Exception as e:
        print(f"[MAIN] Błąd wykonania scrapera eBay: {e}")

    if sort_by == "price_asc":
        all_results.sort(key=lambda x: parse_numeric_price(x.get("price", ""), float('inf')))
    elif sort_by == "price_desc":
        all_results.sort(key=lambda x: parse_numeric_price(x.get("price", ""), -1.0), reverse=True)
    elif sort_by in ["date_asc", "dist_desc"]:
        all_results.reverse()

    print("="*50)
    print(f"[MAIN] PODSUMOWANIE: Łącznie pobrano {len(all_results)} ogłoszeń.")
    print("="*50 + "\n")

    return all_results


if __name__ == "__main__":
    app = ScraperGUI(search_callback=fetch_all_offers)
    app.mainloop()