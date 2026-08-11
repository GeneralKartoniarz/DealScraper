import io
import os
import sys
import threading
import webbrowser
import customtkinter as ctk
from PIL import Image
from curl_cffi import requests
from watchlist import WatchlistManager

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

COLOR_BG = "#11111b"
COLOR_CARD = "#1e1e2e"
COLOR_ACCENT = "#89b4fa"
COLOR_PRICE = "#a6e3a1"
COLOR_TEXT_MUTED = "#a6adc8"

BRAND_COLORS = {
    "OLX": {"bg": "#002f34", "fg": "#23e5db"},
    "ALLEGRO": {"bg": "#ff5a00", "fg": "#ffffff"},
    "EBAY": {"bg": "#0064d2", "fg": "#ffffff"},
    "DEFAULT": {"bg": "#313244", "fg": "#cdd6f4"},
}


class ScraperGUI(ctk.CTk):
    def __init__(self, search_callback):
        super().__init__()

        self.search_callback = search_callback
        self.watchlist_mgr = WatchlistManager()
        
        self.auto_refresh_seconds = 120
        self.time_left = self.auto_refresh_seconds
        self.is_searching = False
        self.selected_topic_id = None

        self.title("DealFinder Desktop v3.0 - Monitor Okazji")
        self.geometry("1280x850")
        self.minsize(1100, 700)
        self.configure(fg_color=COLOR_BG)

        # Kontener Główny - System Zakładek (Tabs)
        self.tabview = ctk.CTkTabview(
            self, 
            fg_color=COLOR_BG, 
            segmented_button_selected_color=COLOR_ACCENT,
            segmented_button_unselected_color=COLOR_CARD,
            segmented_button_unselected_hover_color="#313244"
        )
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)
        self.tabview.pack(fill="both", expand=True, padx=15, pady=10)

        self.tab_search = self.tabview.add("Wyszukiwarka na żywo")
        self.tab_watchlist = self.tabview.add("Stałe obserwowane")

        # Budowa ekranu 1 (Wyszukiwarka)
        self._build_search_tab()

        # Budowa ekranu 2 (Obserwowane)
        self._build_watchlist_tab()

        # Pasek statusu
        self._build_status_bar()

        # Uruchomienie timera
        self._start_timer()

    def _build_search_tab(self):
        header_card = ctk.CTkFrame(self.tab_search, fg_color=COLOR_CARD, corner_radius=16)
        header_card.pack(fill="x", padx=10, pady=(5, 5))

        logo_label = ctk.CTkLabel(header_card, text="⚡ DealFinder", font=("Segoe UI", 20, "bold"), text_color=COLOR_ACCENT)
        logo_label.pack(side="left", padx=20, pady=12)

        self.search_entry = ctk.CTkEntry(
            header_card, 
            placeholder_text="Szukana fraza (np. iPhone 13, obiektyw m42)...", 
            height=40,
            corner_radius=20,
            border_width=1,
            border_color="#45475a",
            fg_color="#181825",
            font=("Segoe UI", 13)
        )
        self.search_entry.pack(side="left", padx=10, pady=12, expand=True, fill="x")
        self.search_entry.bind("<Return>", lambda event: self.trigger_search())

        self.search_button = ctk.CTkButton(
            header_card, 
            text="Szukaj", 
            height=40,
            width=100,
            corner_radius=20,
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            font=("Segoe UI", 13, "bold"),
            command=self.trigger_search
        )
        self.search_button.pack(side="left", padx=5, pady=12)

        # Przycisk "+ Obserwuj"
        self.watch_button = ctk.CTkButton(
            header_card, 
            text="Obserwuj wątek", 
            height=40,
            width=140,
            corner_radius=20,
            fg_color="#313244",
            hover_color="#45475a",
            text_color="#cdd6f4",
            font=("Segoe UI", 12, "bold"),
            command=self._add_current_to_watchlist
        )
        self.watch_button.pack(side="right", padx=(5, 20), pady=12)

        # Pasek filtrów
        self._build_filters_bar(self.tab_search)

        # Lista wyników
        self.results_frame = ctk.CTkScrollableFrame(self.tab_search, fg_color="transparent", label_text="")
        self.results_frame.pack(fill="both", expand=True, padx=10, pady=5)
        self._show_empty_state(self.results_frame, "Wpisz szukaną frazę, aby wyświetlić wyniki na żywo.")

    def _build_filters_bar(self, parent):
        filter_card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=12)
        filter_card.pack(fill="x", padx=10, pady=(0, 10))

        ctk.CTkLabel(filter_card, text="📍 Miasto:", font=("Segoe UI", 11)).pack(side="left", padx=(12, 2), pady=8)
        self.loc_entry = ctk.CTkEntry(filter_card, placeholder_text="np. Warszawa", width=110, height=28)
        self.loc_entry.pack(side="left", padx=(0, 8), pady=8)

        ctk.CTkLabel(filter_card, text="+km:", font=("Segoe UI", 11)).pack(side="left", padx=(4, 2), pady=8)
        self.dist_menu = ctk.CTkOptionMenu(filter_card, values=["0", "10", "15", "30", "50", "100"], width=65, height=28)
        self.dist_menu.pack(side="left", padx=(0, 8), pady=8)

        ctk.CTkLabel(filter_card, text="Od (zł):", font=("Segoe UI", 11)).pack(side="left", padx=(4, 2), pady=8)
        self.min_price_entry = ctk.CTkEntry(filter_card, placeholder_text="Min", width=60, height=28)
        self.min_price_entry.pack(side="left", padx=(0, 6), pady=8)

        ctk.CTkLabel(filter_card, text="Do:", font=("Segoe UI", 11)).pack(side="left", padx=(2, 2), pady=8)
        self.max_price_entry = ctk.CTkEntry(filter_card, placeholder_text="Max", width=60, height=28)
        self.max_price_entry.pack(side="left", padx=(0, 10), pady=8)

        ctk.CTkLabel(filter_card, text="Max ofert:", font=("Segoe UI", 11)).pack(side="left", padx=(4, 2), pady=8)
        self.max_offers_entry = ctk.CTkEntry(filter_card, placeholder_text="50", width=55, height=28)
        self.max_offers_entry.insert(0, "50")
        self.max_offers_entry.pack(side="left", padx=(0, 6), pady=8)

        self.all_offers_chk = ctk.CTkCheckBox(
            filter_card, 
            text="Wszystkie", 
            font=("Segoe UI", 11),
            width=75,
            checkbox_width=17,
            checkbox_height=17,
            command=self._toggle_all_offers
        )
        self.all_offers_chk.pack(side="left", padx=(0, 10), pady=8)

        ctk.CTkLabel(filter_card, text="Sortuj:", font=("Segoe UI", 11)).pack(side="left", padx=(4, 2), pady=8)
        self.sort_menu = ctk.CTkOptionMenu(
            filter_card, 
            values=["Domyślnie", "Najtańsze", "Najdroższe", "Najnowsze", "Najstarsze", "Najbliżej", "Najdalej"], 
            width=105, 
            height=28
        )
        self.sort_menu.pack(side="left", padx=(0, 12), pady=8)

    def _toggle_all_offers(self):
        if self.all_offers_chk.get() == 1:
            self.max_offers_entry.configure(state="disabled")
        else:
            self.max_offers_entry.configure(state="normal")

    # --- TAB 2: Stałe Obserwowane ---
    def _build_watchlist_tab(self):
        paned = ctk.CTkFrame(self.tab_watchlist, fg_color="transparent")
        paned.pack(fill="both", expand=True, padx=5, pady=5)
        paned.grid_columnconfigure(1, weight=1)
        paned.grid_rowconfigure(0, weight=1)

        # Lewa kolumna: Zapisane tematy
        left_panel = ctk.CTkFrame(paned, fg_color=COLOR_CARD, corner_radius=14, width=280)
        left_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=5)
        left_panel.grid_propagate(False)

        lbl_topics = ctk.CTkLabel(left_panel, text="Obserwowane wątki", font=("Segoe UI", 15, "bold"), text_color=COLOR_ACCENT)
        lbl_topics.pack(padx=15, pady=15, anchor="w")

        self.topics_scroll = ctk.CTkScrollableFrame(left_panel, fg_color="transparent")
        self.topics_scroll.pack(fill="both", expand=True, padx=5, pady=(0, 10))

        # Prawa kolumna: Feed nowości
        right_panel = ctk.CTkFrame(paned, fg_color="transparent")
        right_panel.grid(row=0, column=1, sticky="nsew", pady=5)

        self.watchlist_title_lbl = ctk.CTkLabel(right_panel, text="Wybierz wątek z lewej strony lub dodaj nowy", font=("Segoe UI", 15, "bold"))
        self.watchlist_title_lbl.pack(anchor="w", padx=10, pady=(10, 5))

        self.watchlist_feed = ctk.CTkScrollableFrame(right_panel, fg_color="transparent", label_text="")
        self.watchlist_feed.pack(fill="both", expand=True)

        self._refresh_watchlist_sidebar()

    def _refresh_watchlist_sidebar(self):
        """Przerysowuje listę wątków w lewym panelu."""
        for widget in self.topics_scroll.winfo_children():
            widget.destroy()

        if not self.watchlist_mgr.items:
            empty_lbl = ctk.CTkLabel(
                self.topics_scroll, 
                text="Brak obserwowanych wątków.\nDodaj frazę w wyszukiwarce!", 
                font=("Segoe UI", 11), 
                text_color=COLOR_TEXT_MUTED
            )
            empty_lbl.pack(pady=20)
            return

        for item in self.watchlist_mgr.items:
            item_card = ctk.CTkFrame(self.topics_scroll, fg_color="#181825", corner_radius=10)
            item_card.pack(fill="x", pady=4, padx=2)

            btn_title = ctk.CTkButton(
                item_card, 
                text=f"🔍 {item['query']}", 
                anchor="w",
                fg_color="transparent",
                hover_color="#2a2a3c",
                font=("Segoe UI", 12, "bold"),
                command=lambda t_id=item["id"]: self._select_watchlist_topic(t_id)
            )
            btn_title.pack(side="left", fill="x", expand=True, padx=5, pady=5)

            btn_del = ctk.CTkButton(
                item_card, 
                text="❌", 
                width=28, 
                height=28, 
                fg_color="transparent",
                hover_color="#f38ba8",
                text_color="#f38ba8",
                command=lambda t_id=item["id"]: self._remove_from_watchlist(t_id)
            )
            btn_del.pack(side="right", padx=5)

    def _select_watchlist_topic(self, topic_id):
        """Wyświetla nowości dla wybranego wątku."""
        self.selected_topic_id = topic_id
        topic = next((t for t in self.watchlist_mgr.items if t["id"] == topic_id), None)
        if not topic:
            return

        self.watchlist_title_lbl.configure(text=f"Nowości dla wątku: '{topic['query']}' ({len(topic['found_offers'])} ofert)")
        
        for widget in self.watchlist_feed.winfo_children():
            widget.destroy()

        if not topic["found_offers"]:
            self._show_empty_state(self.watchlist_feed, "Czekam na nowe oferty dla tego wątku...\nRobot tła sprawdzi serwisy przy kolejnym odświeżeniu!")
        else:
            for offer in topic["found_offers"]:
                self._create_card(self.watchlist_feed, offer)

    def _add_current_to_watchlist(self):
        """Dodaje aktualne zapytanie z wyszukiwarki do obserwowanych."""
        query = self.search_entry.get().strip()
        if not query:
            self.status_label.configure(text="Wpisz najpierw frazę, którą chcesz obserwować!")
            return

        filters = self._get_current_filters()
        added = self.watchlist_mgr.add_topic(filters)

        if added:
            self.status_label.configure(text=f"✅ Dodano '{query}' do obserwowanych wątków!")
            self._refresh_watchlist_sidebar()
            threading.Thread(target=self._check_single_watchlist_item, args=(added,), daemon=True).start()
        else:
            self.status_label.configure(text=f"Wątek '{query}' jest już na liście obserwowanych.")

    def _remove_from_watchlist(self, topic_id):
        """Usuwa wątek z obserwowanych."""
        self.watchlist_mgr.remove_topic(topic_id)
        self._refresh_watchlist_sidebar()
        if self.selected_topic_id == topic_id:
            for widget in self.watchlist_feed.winfo_children():
                widget.destroy()
            self.watchlist_title_lbl.configure(text="Wybierz wątek z lewej strony")

    def _get_current_filters(self):
        """Pobiera parametry z formularza wyszukiwania."""
        query = self.search_entry.get().strip()
        is_all_offers = bool(self.all_offers_chk.get() == 1)
        raw_max = self.max_offers_entry.get().strip()
        max_offers = int(raw_max) if raw_max.isdigit() and int(raw_max) > 0 else 50

        sort_map = {
            "Domyślnie": "default",
            "Najtańsze": "price_asc",
            "Najdroższe": "price_desc",
            "Najnowsze": "date_desc",
            "Najstarsze": "date_asc",
            "Najbliżej": "dist_asc",
            "Najdalej": "dist_desc"
        }
        sort_by = sort_map.get(self.sort_menu.get(), "default")

        return {
            "query": query,
            "min_price": self.min_price_entry.get().strip(),
            "max_price": self.max_price_entry.get().strip(),
            "location": self.loc_entry.get().strip(),
            "distance": self.dist_menu.get(),
            "max_offers": max_offers,
            "all_offers": is_all_offers,
            "sort_by": sort_by
        }

    # --- OBSŁUGA WYSZUKIWANIA I MONITORINGU ---
    def trigger_search(self):
        query = self.search_entry.get().strip()
        if not query:
            self.status_label.configure(text="Wpisz frazę przed wyszukiwaniem.")
            return

        if self.is_searching:
            return

        self.is_searching = True
        self.search_button.configure(state="disabled", text="Szukam...")
        self.status_label.configure(text=f"Pobieranie danych na żywo dla: '{query}'...")
        self.time_left = self.auto_refresh_seconds

        filters = self._get_current_filters()
        threading.Thread(target=self._worker_search, args=(filters,), daemon=True).start()

    def _worker_search(self, filters):
        results = self.search_callback(filters)
        self.after(0, self._display_live_results, results)

    def _display_live_results(self, results):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            self._show_empty_state(self.results_frame, "Brak wyników spełniających podane kryteria.")
        else:
            for item in results:
                self._create_card(self.results_frame, item)

        self.status_label.configure(text=f"Znaleziono {len(results)} ofert na żywo.")
        self.search_button.configure(state="normal", text="Szukaj")
        self.is_searching = False

    def _check_all_watchlist_items(self):
        """Przechodzi po wszystkich zapisanych wątkach i sprawdza nowości."""
        if not self.watchlist_mgr.items or self.is_searching:
            return

        print("\n[WATCHLIST BROWSER] Rozpoczynam automatyczne sprawdzanie obserwowanych wątków...")
        for topic in list(self.watchlist_mgr.items):
            self._check_single_watchlist_item(topic)

    def _check_single_watchlist_item(self, topic):
        """Sprawdza wątek - pobiera 20 najnowszych ofert i zatrzymuje się na pierwszym znanym linku."""
        check_filters = dict(topic["filters"])
        check_filters["sort_by"] = "date_desc"
        check_filters["max_offers"] = 20
        check_filters["all_offers"] = False

        results = self.search_callback(check_filters)
        if not results:
            return

        seen_set = set(topic["seen_links"])

        if len(seen_set) == 0:
            initial_links = [r["link"] for r in results if r.get("link")]
            self.watchlist_mgr.update_topic_offers(topic["id"], [], initial_links)
            return

        new_discovered = []
        fetched_links = []

        for offer in results:
            link = offer.get("link")
            if not link:
                continue

            fetched_links.append(link)
            if link in seen_set:
                break
            else:
                new_discovered.append(offer)

        self.watchlist_mgr.update_topic_offers(topic["id"], new_discovered, fetched_links)

        if new_discovered:
            print(f"Wykryto {len(new_discovered)} nową/e ofertę/y dla: '{topic['query']}'!")
            self.after(0, lambda: self._notify_watchlist_deals(topic["query"], new_discovered))

        if self.selected_topic_id == topic["id"]:
            self.after(0, lambda: self._select_watchlist_topic(topic["id"]))

    def _notify_watchlist_deals(self, topic_query, new_offers):
        """Wyświetla powiadomienie Toast i dźwięk dla obserwowanego wątku."""
        count = len(new_offers)
        first_offer = new_offers[0]
        title = first_offer.get("title", "Nowa oferta")
        price = first_offer.get("price", "")
        source = first_offer.get("source", "")

        self._play_sound()

        try:
            from plyer import notification
            notification.notify(
                title=f"Obserwowane: {topic_query} ({count} nowa/e)",
                message=f"[{source}] {title} ({price})",
                app_name="DealFinder",
                timeout=7
            )
        except Exception as e:
            print(f"[GUI Toast Error]: {e}")

    def _play_sound(self):
        try:
            if sys.platform == "win32":
                import winsound
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            elif sys.platform == "darwin":
                os.system("afplay /System/Library/Sounds/Glass.aiff &")
            else:
                os.system("paplay /usr/share/sounds/freedesktop/stereo/complete.oga &")
        except Exception:
            pass

    def _show_empty_state(self, parent, message):
        empty_box = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=16)
        empty_box.pack(fill="x", pady=40, padx=20)

        lbl_icon = ctk.CTkLabel(empty_box, text="📦", font=("Segoe UI", 48))
        lbl_icon.pack(pady=(30, 10))

        lbl_msg = ctk.CTkLabel(empty_box, text=message, font=("Segoe UI", 14), text_color=COLOR_TEXT_MUTED)
        lbl_msg.pack(pady=(0, 30))

    def _create_card(self, parent, item):
        card = ctk.CTkFrame(parent, fg_color=COLOR_CARD, corner_radius=14, border_width=1, border_color="#313244")
        card.pack(fill="x", pady=6, padx=5)
        card.grid_columnconfigure(1, weight=1)

        img_container = ctk.CTkFrame(card, width=80, height=80, corner_radius=10, fg_color="#181825")
        img_container.grid(row=0, column=0, padx=12, pady=12)
        img_container.grid_propagate(False)

        img_label = ctk.CTkLabel(img_container, text="🖼️", font=("Segoe UI", 20))
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        if item.get("image_url"):
            threading.Thread(target=self._load_image_async, args=(item["image_url"], img_label), daemon=True).start()

        details_frame = ctk.CTkFrame(card, fg_color="transparent")
        details_frame.grid(row=0, column=1, sticky="nsew", pady=12)

        meta_row = ctk.CTkFrame(details_frame, fg_color="transparent")
        meta_row.pack(fill="x", anchor="w")

        source_name = str(item.get("source", "Inny")).upper()
        brand_style = BRAND_COLORS.get(source_name, BRAND_COLORS["DEFAULT"])

        source_badge = ctk.CTkFrame(meta_row, fg_color=brand_style["bg"], corner_radius=6)
        source_badge.pack(side="left")
        
        badge_lbl = ctk.CTkLabel(source_badge, text=source_name, font=("Segoe UI", 10, "bold"), text_color=brand_style["fg"])
        badge_lbl.pack(padx=8, pady=2)

        loc_lbl = ctk.CTkLabel(meta_row, text=f"📍 {item.get('location', 'Brak lokalizacji')}", font=("Segoe UI", 11), text_color=COLOR_TEXT_MUTED)
        loc_lbl.pack(side="left", padx=10)

        title_lbl = ctk.CTkLabel(
            details_frame, 
            text=item.get("title", "Brak tytułu"), 
            font=("Segoe UI", 13, "bold"),
            anchor="w",
            justify="left",
            wraplength=450
        )
        title_lbl.pack(fill="x", pady=(6, 0), anchor="w")

        action_frame = ctk.CTkFrame(card, fg_color="transparent")
        action_frame.grid(row=0, column=2, padx=15, pady=12, sticky="e")

        price_lbl = ctk.CTkLabel(action_frame, text=item.get("price", "Brak ceny"), font=("Segoe UI", 16, "bold"), text_color=COLOR_PRICE)
        price_lbl.pack(anchor="e", pady=(0, 4))

        open_btn = ctk.CTkButton(
            action_frame, 
            text="Zobacz ofertę ↗", 
            width=110,
            height=32,
            corner_radius=8,
            fg_color="#313244",
            hover_color="#45475a",
            text_color="#cdd6f4",
            font=("Segoe UI", 11, "bold"),
            command=lambda url=item.get("link"): webbrowser.open(url) if url else None
        )
        open_btn.pack(anchor="e")

    def _load_image_async(self, image_url, target_label):
        """Asynchroniczne pobieranie miniatury z wykorzystaniem curl_cffi i trzymaniem referencji dla GC."""
        if not image_url or image_url.startswith("data:"):
            return

        if image_url.startswith("//"):
            image_url = "https:" + image_url

        try:
            response = requests.get(image_url, impersonate="chrome", timeout=8)
            if response.status_code == 200:
                img_data = Image.open(io.BytesIO(response.content)).convert("RGBA")
                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(80, 80))

                def update_ui():
                    target_label._image_ref = ctk_img
                    target_label.configure(image=ctk_img, text="")

                self.after(0, update_ui)
        except Exception:
            pass

    def _build_status_bar(self):
        status_bar = ctk.CTkFrame(self, fg_color="transparent")
        status_bar.pack(fill="x", padx=25, pady=(0, 5))

        self.status_label = ctk.CTkLabel(status_bar, text="Stan: Gotowy", font=("Segoe UI", 12), text_color=COLOR_TEXT_MUTED)
        self.status_label.pack(side="left")

        self.timer_badge = ctk.CTkFrame(status_bar, fg_color="#313244", corner_radius=12)
        self.timer_badge.pack(side="right")

        self.timer_label = ctk.CTkLabel(
            self.timer_badge, 
            text=f"Auto-sprawdzanie za: {self.time_left}s", 
            font=("Segoe UI", 11, "bold"),
            text_color="#cdd6f4"
        )
        self.timer_label.pack(padx=12, pady=4)

    def _start_timer(self):
        """Timer tła - co 2 minuty uruchamia sprawdzanie WSZYSTKICH obserwowanych wątków."""
        def timer_tick():
            self.time_left -= 1
            if self.time_left <= 0:
                self.time_left = self.auto_refresh_seconds
                threading.Thread(target=self._check_all_watchlist_items, daemon=True).start()
            else:
                self.timer_label.configure(text=f"Auto-sprawdzanie za: {self.time_left}s")
            self.after(1000, timer_tick)

        self.after(1000, timer_tick)