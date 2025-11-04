# AI-Visual-Data-Reporter

## Cel
Opisuje wykresy z raportów (PNG, PDF).

## Zakres
- Zebranie zestawu obrazów wykresów (PNG, PDF).
- Implementacja odczytu obrazu (Vision SDK – OCR + obiekty).
- Integracja z Azure OpenAI SDK (prompt do analizy i streszczenia).
- Testy i walidacja opisów (poprawność i spójność).
- Przygotowanie prostego interfejsu (Streamlit / Flask).
- Prezentacja demo i dokumentacja projektu.

**Usługi:** Vision SDK, Azure OpenAI SDK.

**Efekt:** system wyjaśniający raporty wizualne (np. „Wykres pokazuje wzrost sprzedaży w Q2 o 15%").

## Przykłądowe źródła do wykresów: 
- https://data.gov/
- https://ourworldindata.org/
- https://public.tableau.com/app/learn/sample-data
- https://matplotlib.org/stable/gallery/index.html
- https://seaborn.pydata.org/examples/index.html
- https://pandas.pydata.org/docs/user_guide/visualization.html

## Testy i walidacja opisów 
- możemy wykorzystać źródła, które posiadają również pliki csv, xls, json (bardziej pewne obliczenia)
- możemy pobierać dane w formacie csv/xml i samemu tworzyć wykresy
- Inne pomysły ?

# Interfejs
- https://streamlit.io/
- https://flask.palletsprojects.com/en/stable/

# How to use it? 

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt 
streamlit run app.py --server.port 8202
```