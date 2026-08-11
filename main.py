import time
from gui import ScraperGUI
from scrapers.olx import scrape_olx
from scrapers.ebay import scrape_ebay
from scrapers.allegro import scrape_allegro


def fetch_all_offers(filters: dict) -> list[dict]:
    query = filters.get("query", "").strip()
    print("\n" + "="*50)
    print(f"[MAIN] WYSZUKIWANIE DLA FRAZY: '{query}'")
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
            all_offers=filters["all_offers"]
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
            all_offers=filters["all_offers"]
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
            all_offers=filters["all_offers"]
        )
        print(f"[MAIN] eBay -> Pobrano: {len(ebay_results)} ofert.")
        all_results.extend(ebay_results)
    except Exception as e:
        print(f"[MAIN] Błąd wykonania scrapera eBay: {e}")

    print("="*50)
    print(f"[MAIN] PODSUMOWANIE: Łącznie pobrano {len(all_results)} ogłoszeń.")
    print("="*50 + "\n")

    return all_results


if __name__ == "__main__":
    app = ScraperGUI(search_callback=fetch_all_offers)
    app.mainloop()