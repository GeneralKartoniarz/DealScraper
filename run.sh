#!/bin/bash

if [ ! -d "venv" ]; then
    echo "[INFO] Tworzenie wirtualnego środowiska venv..."
    python3 -m venv venv
fi

source venv/bin/activate

echo "[INFO] Sprawdzanie i instalacja wymaganych bibliotek..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[INFO] Uruchamianie DealFinder..."
python main.py