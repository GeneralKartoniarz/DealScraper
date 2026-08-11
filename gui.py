import io
import threading
import webbrowser
import customtkinter as ctk
from PIL import Image
import requests

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
    "DEFAULT": {"bg": "#313244", "fg": "#cdd6f4"}
}


class ScraperGUI(ctk.CTk):
    def __init__(self, search_callback):
        super().__init__()

        self.search_callback = search_callback
        self.auto_refresh_seconds = 120
        self.time_left = self.auto_refresh_seconds
        self.is_searching = False

        self.title("DealFinder Desktop v2.1")
        self.geometry("1180x800")
        self.minsize(1050, 650)
        self.configure(fg_color=COLOR_BG)

        self._build_header()
        self._build_filters_bar()
        self._build_status_bar()

        self.results_frame = ctk.CTkScrollableFrame(self, fg_color="transparent", label_text="")
        self.results_frame.pack(fill="both", expand=True, padx=20, pady=(0, 15))

        self._show_empty_state("Wpisz szukaną frazę i ustaw filtry, aby rozpocząć monitoring.")
        self._start_timer()

    def _build_header(self):
        header_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=16)
        header_card.pack(fill="x", padx=20, pady=(15, 5))

        logo_label = ctk.CTkLabel(
            header_card, 
            text="⚡ DealFinder", 
            font=("Segoe UI", 20, "bold"),
            text_color=COLOR_ACCENT
        )
        logo_label.pack(side="left", padx=20, pady=12)

        self.search_entry = ctk.CTkEntry(
            header_card, 
            placeholder_text="🔍 Szukana fraza (np. iPhone 13, Rower)...", 
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
            width=110,
            corner_radius=20,
            fg_color=COLOR_ACCENT,
            text_color="#11111b",
            hover_color="#b4befe",
            font=("Segoe UI", 13, "bold"),
            command=self.trigger_search
        )
        self.search_button.pack(side="right", padx=(5, 20), pady=12)

    def _build_filters_bar(self):
        filter_card = ctk.CTkFrame(self, fg_color=COLOR_CARD, corner_radius=12)
        filter_card.pack(fill="x", padx=20, pady=(0, 10))

        # 1. Lokalizacja
        ctk.CTkLabel(filter_card, text="📍Miasto:", font=("Segoe UI", 11)).pack(side="left", padx=(15, 2), pady=8)
        self.loc_entry = ctk.CTkEntry(filter_card, placeholder_text="np. Warszawa", width=120, height=28)
        self.loc_entry.pack(side="left", padx=(0, 10), pady=8)

        # 2. Dystans (Promień)
        ctk.CTkLabel(filter_card, text="+km:", font=("Segoe UI", 11)).pack(side="left", padx=(5, 2), pady=8)
        self.dist_menu = ctk.CTkOptionMenu(
            filter_card, 
            values=["0", "10", "15", "30", "50", "100"], 
            width=70, 
            height=28
        )
        self.dist_menu.pack(side="left", padx=(0, 10), pady=8)

        # 3. Cena Od
        ctk.CTkLabel(filter_card, text="Od (zł):", font=("Segoe UI", 11)).pack(side="left", padx=(5, 2), pady=8)
        self.min_price_entry = ctk.CTkEntry(filter_card, placeholder_text="Min", width=65, height=28)
        self.min_price_entry.pack(side="left", padx=(0, 10), pady=8)

        # 4. Cena Do
        ctk.CTkLabel(filter_card, text="Do:", font=("Segoe UI", 11)).pack(side="left", padx=(2, 2), pady=8)
        self.max_price_entry = ctk.CTkEntry(filter_card, placeholder_text="Max", width=65, height=28)
        self.max_price_entry.pack(side="left", padx=(0, 15), pady=8)

        # 5. Ilość ogłoszeń
        ctk.CTkLabel(filter_card, text="Max ofert:", font=("Segoe UI", 11)).pack(side="left", padx=(5, 2), pady=8)
        self.max_offers_entry = ctk.CTkEntry(filter_card, placeholder_text="50", width=60, height=28)
        self.max_offers_entry.insert(0, "50")
        self.max_offers_entry.pack(side="left", padx=(0, 6), pady=8)

        # 6. Checkbox Wszystkie
        self.all_offers_chk = ctk.CTkCheckBox(
            filter_card, 
            text="Wszystkie", 
            font=("Segoe UI", 11),
            width=80,
            checkbox_width=18,
            checkbox_height=18,
            command=self._toggle_all_offers
        )
        self.all_offers_chk.pack(side="left", padx=(0, 15), pady=8)

    def _toggle_all_offers(self):
        """Włącza/wyłącza pole max ofert w zależności od checkboxa."""
        if self.all_offers_chk.get() == 1:
            self.max_offers_entry.configure(state="disabled")
        else:
            self.max_offers_entry.configure(state="normal")

    def _build_status_bar(self):
        status_bar = ctk.CTkFrame(self, fg_color="transparent")
        status_bar.pack(fill="x", padx=25, pady=(0, 5))

        self.status_label = ctk.CTkLabel(status_bar, text="Stan: Gotowy", font=("Segoe UI", 12), text_color=COLOR_TEXT_MUTED)
        self.status_label.pack(side="left")

        self.timer_badge = ctk.CTkFrame(status_bar, fg_color="#313244", corner_radius=12)
        self.timer_badge.pack(side="right")

        self.timer_label = ctk.CTkLabel(
            self.timer_badge, 
            text=f"🔄 Odświeżanie za: {self.time_left}s", 
            font=("Segoe UI", 11, "bold"),
            text_color="#cdd6f4"
        )
        self.timer_label.pack(padx=12, pady=4)

    def trigger_search(self):
        query = self.search_entry.get().strip()
        if not query:
            self.status_label.configure(text="Wpisz frazę przed uruchomieniem wyszukiwania.")
            return

        if self.is_searching:
            return

        self.is_searching = True
        self.search_button.configure(state="disabled", text="Szukam...")
        self.status_label.configure(text=f"🔎 Pobieranie danych dla: '{query}'...")
        self.time_left = self.auto_refresh_seconds

        is_all_offers = bool(self.all_offers_chk.get() == 1)
        raw_max = self.max_offers_entry.get().strip()
        max_offers = int(raw_max) if raw_max.isdigit() and int(raw_max) > 0 else 50

        filters = {
            "query": query,
            "min_price": self.min_price_entry.get().strip(),
            "max_price": self.max_price_entry.get().strip(),
            "location": self.loc_entry.get().strip(),
            "distance": self.dist_menu.get(),
            "max_offers": max_offers,
            "all_offers": is_all_offers
        }

        threading.Thread(target=self._worker_search, args=(filters,), daemon=True).start()

    def _worker_search(self, filters):
        results = self.search_callback(filters)
        self.after(0, self._display_results, results)

    def _display_results(self, results):
        for widget in self.results_frame.winfo_children():
            widget.destroy()

        if not results:
            self._show_empty_state("Brak wyników spełniających podane kryteria.")
        else:
            for item in results:
                self._create_card(item)

        self.status_label.configure(text=f"Znaleziono {len(results)} pasujących ofert.")
        self.search_button.configure(state="normal", text="Szukaj")
        self.is_searching = False

    def _show_empty_state(self, message):
        empty_box = ctk.CTkFrame(self.results_frame, fg_color=COLOR_CARD, corner_radius=16)
        empty_box.pack(fill="x", pady=40, padx=20)

        lbl_icon = ctk.CTkLabel(empty_box, text="📦", font=("Segoe UI", 48))
        lbl_icon.pack(pady=(30, 10))

        lbl_msg = ctk.CTkLabel(empty_box, text=message, font=("Segoe UI", 14), text_color=COLOR_TEXT_MUTED)
        lbl_msg.pack(pady=(0, 30))

    def _create_card(self, item):
        card = ctk.CTkFrame(
            self.results_frame, 
            fg_color=COLOR_CARD, 
            corner_radius=14,
            border_width=1,
            border_color="#313244"
        )
        card.pack(fill="x", pady=6, padx=5)
        card.grid_columnconfigure(1, weight=1)

        # Miniaturka
        img_container = ctk.CTkFrame(card, width=80, height=80, corner_radius=10, fg_color="#181825")
        img_container.grid(row=0, column=0, padx=12, pady=12)
        img_container.grid_propagate(False)

        img_label = ctk.CTkLabel(img_container, text="🖼️", font=("Segoe UI", 20))
        img_label.place(relx=0.5, rely=0.5, anchor="center")

        if item.get("image_url"):
            threading.Thread(
                target=self._load_image_async, 
                args=(item["image_url"], img_label), 
                daemon=True
            ).start()

        # Detale
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

        # Cena i Przycisk
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
        try:
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(image_url, headers=headers, timeout=5)
            if response.status_code == 200:
                img_data = Image.open(io.BytesIO(response.content))
                ctk_img = ctk.CTkImage(light_image=img_data, dark_image=img_data, size=(80, 80))
                self.after(0, lambda: target_label.configure(image=ctk_img, text=""))
        except Exception:
            pass

    def _start_timer(self):
        def timer_tick():
            if not self.is_searching and self.search_entry.get().strip():
                self.time_left -= 1
                if self.time_left <= 0:
                    self.trigger_search()
                else:
                    self.timer_label.configure(text=f"Odświeżanie za: {self.time_left}s")
            self.after(1000, timer_tick)

        self.after(1000, timer_tick)