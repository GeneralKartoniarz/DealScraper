import hashlib
import json
import os
import time

WATCHLIST_FILE = "watchlist.json"


def get_clean_url(url: str) -> str:
    """Usuwa z linku zmienne śledzące, parametry wyszukiwania i znaki zapytania."""
    if not url:
        return ""
    clean = url.split("?")[0].split("#")[0].strip().rstrip("/")
    return clean


def hash_link(link: str) -> str:
    """Generuje 12-znakowy hash MD5 z czystego adresu ogłoszenia."""
    clean = get_clean_url(link)
    if not clean:
        return ""
    return hashlib.md5(clean.encode("utf-8")).hexdigest()[:12]


class WatchlistManager:
    def __init__(self):
        self.items = self.load_watchlist()

    def load_watchlist(self) -> list[dict]:
        """Wczytuje listę obserwowanych wątków z pliku JSON."""
        if not os.path.exists(WATCHLIST_FILE):
            return []
        try:
            with open(WATCHLIST_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Watchlist] Błąd odczytu pliku: {e}")
            return []

    def save_watchlist(self):
        """Zapisuje obecny stan do pliku JSON."""
        try:
            with open(WATCHLIST_FILE, "w", encoding="utf-8") as f:
                json.dump(self.items, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[Watchlist] Błąd zapisu pliku: {e}")

    def add_topic(self, filters: dict, initial_offers: list[dict] = None) -> dict:
        """Dodaje wątek i zapisuje czyste kody MD5 bez śmieci URL."""
        query = filters.get("query", "").strip()
        if not query:
            return None

        for item in self.items:
            if item["query"].lower() == query.lower():
                return None

        offers = initial_offers or []
        seen_hashes = [hash_link(o["link"]) for o in offers if o.get("link")]

        new_topic = {
            "id": str(int(time.time())),
            "query": query,
            "filters": filters,
            "seen_links": seen_hashes[:200],
            "found_offers": []            
        }
        self.items.append(new_topic)
        self.save_watchlist()
        return new_topic

    def remove_topic(self, topic_id: str):
        """Usuwa wątek z obserwowanych."""
        self.items = [item for item in self.items if item["id"] != topic_id]
        self.save_watchlist()

    def clear_topic_offers(self, topic_id: str):
        """Czyści listę zgromadzonych ofert dla danego wątku."""
        for item in self.items:
            if item["id"] == topic_id:
                item["found_offers"] = []
                break
        self.save_watchlist()

    def add_new_offers(self, topic_id: str, new_offers: list[dict]):
        """Dopisuje unikalne nowe oferty i aktualizuje kody w pamięci."""
        for item in self.items:
            if item["id"] == topic_id:
                for offer in reversed(new_offers):
                    link = offer.get("link")
                    if link:
                        h = hash_link(link)
                        if h not in item["seen_links"]:
                            item["seen_links"].insert(0, h)
                            item["found_offers"].insert(0, offer)

                item["seen_links"] = item["seen_links"][:200]
                item["found_offers"] = item["found_offers"][:50]
                break
        self.save_watchlist()