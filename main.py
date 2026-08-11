from gui import ScraperGUI
from scrapers.olx import scrape_olx
from scrapers.ebay import scrape_ebay
from scrapers.allegro import scrape_allegro


def fetch_all_offers(filters: dict) -> list[dict]:
    """Pobiera dane z OLX, eBay oraz Allegro, a następnie łączy je w jedną listę."""
    print(f"[MAIN] Rozpoczynam wyszukiwanie w serwisach OLX, eBay i Allegro dla: '{filters['query']}'...")

    all_results = []

    # 1. Scraper OLX
    try:
        olx_results = scrape_olx(
            query=filters["query"],
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            location=filters["location"],
            distance=filters["distance"],
            max_offers=filters["max_offers"],
            all_offers=filters["all_offers"]
        )
        print(f"[MAIN] OLX zwrócił {len(olx_results)} ofert.")
        all_results.extend(olx_results)
    except Exception as e:
        print(f"[MAIN] Błąd podczas pobierania z OLX: {e}")

    # 2. Scraper eBay
    try:
        ebay_results = scrape_ebay(
            query=filters["query"],
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            location=filters["location"],
            distance=filters["distance"],
            max_offers=filters["max_offers"],
            all_offers=filters["all_offers"]
        )
        print(f"[MAIN] eBay zwrócił {len(ebay_results)} ofert.")
        all_results.extend(ebay_results)
    except Exception as e:
        print(f"[MAIN] Błąd podczas pobierania z eBay: {e}")

    # 3. Scraper Allegro
    try:
        allegro_results = scrape_allegro(
            query=filters["query"],
            min_price=filters["min_price"],
            max_price=filters["max_price"],
            location=filters["location"],
            distance=filters["distance"],
            max_offers=filters["max_offers"],
            all_offers=filters["all_offers"]
        )
        print(f"[MAIN] Allegro zwrócił {len(allegro_results)} ofert.")
        all_results.extend(allegro_results)
    except Exception as e:
        print(f"[MAIN] Błąd podczas pobierania z Allegro: {e}")

    print(f"[MAIN] Łącznie pobrano {len(all_results)} ogłoszeń z 3 serwisów.")
    return all_results


if __name__ == "__main__":
    app = ScraperGUI(search_callback=fetch_all_offers)
    app.mainloop()