# AI-Visual-Data-Reporter

## Cel
Celem projektu było stworzenie systemu, który opisuje wykresy z raportów (PNG, PDF).

## Zakres
- Zebranie zestawu obrazów wykresów (PNG, PDF).
- Implementacja odczytu obrazu (Vision SDK – OCR + obiekty).
- Integracja z Azure OpenAI SDK (prompt do analizy i streszczenia).
- Testy i walidacja opisów (poprawność i spójność).
- Przygotowanie prostego interfejsu (Streamlit).
- Prezentacja demo i dokumentacja projektu.

**Usługi:** Vision SDK, Azure OpenAI SDK.

**Efekt:** system wyjaśniający raporty wizualne (np. „Wykres pokazuje wzrost sprzedaży w Q2 o 15%").

## 🏗️ Struktura Projektu

```
AI-VISUAL-DATA-REPORTER/
│
├── 📄 README.md                     # Główna dokumentacja
├── 📄 QUICK_START.md                # Szybki przewodnik uruchomienia
├── 📄 AI102_EXAM_NOTES.md           # Notatki egzaminacyjne + wskazówki
│
├── ⚙️ config.py                    # Konfiguracja klientów + walidacja credentials
├── 📋 requirements.txt              # Zależności Python
│
├── 🎯 chart_assistant.py           # Plik zawierający logikę analizy wykresów: Azure Computer Vision OCR + GPT-4 Vision do ekstrakcji danych i interpretacji.
├── 📝 app.py                       # Główny plik aplikacji Streamlit z interfejsem użytkownika do uploadu i analizy wykresów (obrazy + PDF).
|
└── 📂 tests                        
    ├── 📂📈 advanced_charts                         # Folder z przykładowymi plikami do testów (bardziej złożone)
    ├── 📂 advanced_tests 
    │   ├── 📊 load_advanced_test_cases.py            # Plik do ładowania wykresów i ich opisów
    │   ├── 📊 run_chart_analysis_tests.py            # Plik z testami i funkcjami pomocniczymi do testów
    │   └── 📄 test_results.json                      # Plik z rezultatami testów sekcji złożonych wykresów
    └── 📂 simple_tests
        ├── 📂📈 simple_charts                       # Folder z przykładowymi plikami do testów (mniej złożone)
        ├── 📊 run_test_and_validation.py            # Plik z testami wyników analizy
        ├── 📊 test_cases.py                         # Plik z informacjami o przypadkach testowych
        └── 📊 utilities.py                          # Plik z funkcjami pomocniczymi do testów

```

## Opis aplikacji

W aplikacji wykorzystano Azure Vision SDK oraz OpenAI SDK. 

Przygotowano prosty interfejs z wykorzystaniem Streamlit (plik app.py), który umożliwia upload wykresów i konwersję stron PDF na obrazy. Założono, że program będzie przyjmował pliki w formatach "png", "jpg", "jpeg" i "pdf" oraz, że można dołączyć więcej niż jeden wykres. W przypadku plików PDF wykorzystano moduł PyMuPDF w celu przetworzenia ich do formatu jpg. 

Wstępnie przetworzone obrazy są następnie przekazywane do klasy ChartsAssistant (z pliku chart_assistant.py), gdzie wykorzystano Azure Computer Vision OCR do ekstrakcji danych oraz GPT-4 Vision do analizy wizualne i interpretacji. Dodano również możliwość uzyskania kontekstowych odpowiedzi na pytania użytkownika odnośnie wgranych plików.

## Uruchomienie aplikacji <a id="uruchomienie-id"></a>

```
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt 
streamlit run app.py --server.port 8202
```

Poniżej znajduje się przykładowy zrzut ekranu oraz link do dysku z nagraniem przedstawiającym zapytanie do naszego asystenta oraz jego odpowiedź.
Na nagraniu i zdjęciu zaprezentowano jego działanie na przykładowym wykresie.
<img width="1819" height="874" alt="image" src="https://github.com/user-attachments/assets/759f91b1-912e-4185-a651-e71b86b6bc7e" />
https://drive.google.com/file/d/1yzIft0ywEZVOZlIuaVvI1KwqYzyVW4dF/view?usp=sharing

Kolejne nagrania przedstawiają przetwarzanie pdf'a zawierającego kilka wykresów:
- Pdf złożony z trzech wykresów: https://drive.google.com/file/d/1IFsUjofndI_tfQBg6qesfXk7UXC0zWAJ/view?usp=sharing

- Pdf złożony z sześciu wykresów: https://drive.google.com/file/d/1Wgm0eaWNilz6Wp23UWLbwsU7O6sBFW2B/view?usp=sharing

## Informacje o zbiorach plików

W projekcie takim jak AI Visual Data Reporter, gdzie testujemy rozpoznawanie i opisywanie wykresów (Vision + OpenAI), kluczowa jest różnorodność i wystarczająca liczba przykładów do walidacji działania.


### 🎯 Cel zbioru

Stworzyć zestaw obrazów (PNG, PDF) przedstawiających różne typy wykresów, które system ma umieć:

- rozpoznać,

- odczytać (OCR + struktura),

- opisać językiem naturalnym,

- porównać między sobą (analiza wielu wykresów asynchronicznie).


AI Visual Data Reporter ma ambicję:

-> rozpoznawać różne formy wizualnej informacji,

-> opisywać ich strukturę,

-> tłumaczyć ich sens użytkownikowi


### 📊 Optymalna liczba wykresów

💡 25–30 wykresów to idealna liczba, by:

- pokryć wszystkie typy wykresów,

- dać zespołowi materiał do testów i walidacji (Angelika),

- zachować rozsądną wielkość pliku datasetu (dla OpenAI Vision i Document Intelligence).


### 📂 Struktura zbioru (propozycja)

Podziel wykresy na 5 kategorii (różne typy danych i wizualizacji):

| Kategoria | Typ wykresu | Liczba |
|-----------|-------------|--------|
| 📈 Trendy w czasie | liniowy, obszarowy, ze wskaźnikiem trendu | 6 |
| 📊 Porównania | słupkowy, kolumnowy, grupowany, poziomy | 6 |
| 🥧 Udziały procentowe | kołowy, pierścieniowy, „treemap" | 4 |
| 🌍 Dane złożone | wykres punktowy, bąbelkowy, mapa cieplna | 4 |
| 💼 Raporty finansowe | przychody, zyski, sprzedaż kwartalna, KPI dashboardy | 5–6 |
| 👉 Diagramy procesowe | schematy blokowe, (flowcharts) | – |
||


Razem: ~25–30 wykresów.


### Założenia naszego zbioru

- 3-4 źródła (np. Statista, Kaggle, raporty roczne firm, Google Charts demo), by dane nie były jednorodne.

- Część wykresów w języku angielskim, część po polsku – przetestuje to OCR.

- Zostały dodane 2–3 wykresy z błędami (np. rozmazane, z niskim kontrastem) – celem testów walidacyjnych.

- Format: PNG  + przykłady w PDF

### Testy i walidacja rozwiązania
Testy podzielono na dwie grupy ze względu na ich zaawansowanie: wykresy proste i wykresy bardziej złożone.

#### Działanie testów z grupy pierwszej - przykładowy zrzut ekranu oraz nagranie:
<img width="1639" height="819" alt="image" src="https://github.com/user-attachments/assets/a5bc1009-c310-4e9b-aacb-405e625e79f0" />
https://drive.google.com/file/d/121Z1c-pCiEkWv66TfLavsvV1ZJBx2Uki/view?usp=sharing

####  Działanie testów z grupy drugiej (wykresy bardziej złożone)
- Poniżej przedstawiono typy wykresów, które zostaną użyte w testach poprawności rezultatów naszej aplikacji:
<img width="374" height="487" alt="image" src="https://github.com/user-attachments/assets/2ddd2c52-1cd4-4ba2-ab5d-77479aafd6cc" />

- Nagranie przedstawiające przebieg testów zautomatyzowanych:

https://drive.google.com/file/d/1aqZ-FCZqBr4ezDGEhYs-kBegjoBp3y_Z/view?usp=sharing

- Wyniki testów:
<img width="910" height="874" alt="image" src="https://github.com/user-attachments/assets/e0863a9b-3b33-4bd6-91cb-3162a7bbfa9f" />

Testy pdf'ów złożonych z kilku wykresów w jednym pliku zostały przetestowane manualnie (Patrz: [Jump to Uruchomienie aplikacji](#uruchomienie-id))


### 📦 Podsumowanie

✅ Minimum: 20 wykresów (wersja skrócona, testowa)

🌟 Optimum: 25–30 wykresów (pełny, dobrze wykonany zbiór)


🚀 Ambitnie: 40 wykresów (do późniejszej walidacji modelu asynchronicznego)



