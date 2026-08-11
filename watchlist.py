import json
import os
import time

WATCHLIST_FILE = "watchlist.json"


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

    def add_topic(self, filters: dict) -> dict:
        """Dodaje nową frazę z filtrami do listy obserwowanych."""
        query = filters.get("query", "").strip()
        if not query:
            return None

        for item in self.items:
            if item["query"].lower() == query.lower():
                return None

        new_topic = {
            "id": str(int(time.time())),
            "query": query,
            "filters": filters,
            "seen_links": [],
            "found_offers": []
        }
        self.items.append(new_topic)
        self.save_watchlist()
        return new_topic

    def remove_topic(self, topic_id: str):
        """Usuwa wątek z obserwowanych."""
        self.items = [item for item in self.items if item["id"] != topic_id]
        self.save_watchlist()

    def update_topic_offers(self, topic_id: str, new_offers: list[dict], fetched_links: list[str]):
        """Aktualizuje historię linków (max 200) i dopisuje wyłapane nowości na początek listy podglądu."""
        for item in self.items:
            if item["id"] == topic_id:
                for link in reversed(fetched_links):
                    if link not in item["seen_links"]:
                        item["seen_links"].insert(0, link)

                item["seen_links"] = item["seen_links"][:200]

                for offer in new_offers:
                    item["found_offers"].insert(0, offer)

                item["found_offers"] = item["found_offers"][:100]
                break
        self.save_watchlist()