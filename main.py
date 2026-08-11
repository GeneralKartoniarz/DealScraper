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
    query = filters.get("query", "")
    enabled = filters.get("enabled_sources", ["OLX", "ALLEGRO", "EBAY"])
    
    all_results = []

    if "OLX" in enabled:
        olx_res = scrape_olx(
            query=query,
            min_price=filters.get("min_price", ""),
            max_price=filters.get("max_price", ""),
            location=filters.get("location", ""),
            max_offers=filters.get("max_offers", 50),
            all_offers=filters.get("all_offers", False),
            sort_by=filters.get("sort_by", "default")
        )
        all_results.extend(olx_res)

    if "ALLEGRO" in enabled:
        allegro_res = scrape_allegro(
            query=query,
            min_price=filters.get("min_price", ""),
            max_price=filters.get("max_price", ""),
            location=filters.get("location", ""),
            max_offers=filters.get("max_offers", 50),
            all_offers=filters.get("all_offers", False),
            sort_by=filters.get("sort_by", "default")
        )
        all_results.extend(allegro_res)

    if "EBAY" in enabled:
        ebay_res = scrape_ebay(
            query=query,
            min_price=filters.get("min_price", ""),
            max_price=filters.get("max_price", ""),
            location=filters.get("location", ""),
            max_offers=filters.get("max_offers", 50),
            all_offers=filters.get("all_offers", False),
            sort_by=filters.get("sort_by", "default")
        )
        all_results.extend(ebay_res)

    return all_results


if __name__ == "__main__":
    app = ScraperGUI(search_callback=fetch_all_offers)
    app.mainloop()