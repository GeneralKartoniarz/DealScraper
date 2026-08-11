@echo off
if not exist venv (
    echo Tworzenie...
    python -m venv venv
)

call venv\Scripts\activate

echo Sprawdzanie i instalacja bibliotek...
pip install -r requirements.txt --quiet

echo Uruchamianie aplikacji...
python main.py
pause