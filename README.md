# DealScraper Desktop

![Python Version](https://img.shields.io/badge/python-3.10%2B-blue.svg)
![GUI Framework](https://img.shields.io/badge/UI-CustomTkinter-blueviolet.svg)
![Scraper Status](https://img.shields.io/badge/Scraper-OLX%20%7C%20Allegro%20%7C%20eBay-brightgreen.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

Aplikacja zbiera oferty z 3 portali w jednym miejscu, wyświetla je w estetycznym widoku kart (*Dark Dashboard*), dociąga zdjęcia oraz automatycznie odświeża wyniki co **2 minuty**.

## Kluczowe Funkcje

-  **Multi-search:** Jednoczesne przeszukiwanie OLX, Allegro Lokalnie oraz eBay.
-  **Modern Dark UI:** Estetyczny interfejs stworzony w `CustomTkinter` z dedykowanymi badge'ami kolorystycznymi dla każdego serwisu.
-  **Auto-odświeżanie:** Licznik tła automatycznie ponawia wyszukiwanie co 120 sekund.
-  **Zaawansowane Filtrowanie:**
  - Ceny minimalne i maksymalne (`Od / Do`).
  - Lokalizacja i promień wyszukiwania (`+km`).
  - Precyzyjny limit ofert lub opcja pobierania **wszystkich dostępnych ogłoszeń**.
  - Sortowanie (Najtańsze, Najdroższe, Najnowsze, Najbliżej).
-  **Anti-Bot Bypass:** Wykorzystanie `curl-cffi` (impersonacja profilu TLS Google Chrome) pozwala bezproblemowo omijać zabezpieczenia Cloudflare i Akamai bez ryzyka blokad IP.
-  **Podgląd Zdjęć:** Asynchroniczne pobieranie i skalowanie miniaturek bez zawieszania interfejsu.

##  Szybki Start
### Wymagania:
- Zainstalowany **Python 3.10** lub nowszy ([Pobierz Pythona](https://www.python.org/downloads/)).
### Instrukcja:
1. **Sklonuj repozytorium**
2. **Uruchom plik run.bat**
