# Code Review: AI Visual Data Reporter

**Data:** 18 listopada 2025, Ania Schiller
**Linie kodu:** ~802 linii Python  
**Stack:** Azure Computer Vision, Azure OpenAI (GPT-4 Vision), Streamlit, PyMuPDF

---

## 1. ARCHITEKTURA I STRUKTURA PROJEKTU

### Mocne strony:

- **Czysty use case**: OCR + GPT-4 Vision do analizy wykresów
- **Najprostsza struktura** ze wszystkich 3 projektów
- **Testy są obecne!** Folder `tests/` z test cases
- **Dobrze zorganizowana dokumentacja** w README

### Problemy:

**P1: Flat structure - wszystko w root**

```
Obecna struktura:
.
├── app.py
├── chart_assistant.py
├── config.py
└── tests/
    ├── advanced_tests/
    └── simple_tests/

Powinna być:
src/
├── __init__.py
├── core/
│   ├── __init__.py
│   └── chart_assistant.py
├── config/
│   ├── __init__.py
│   └── azure_config.py
└── ui/
    ├── __init__.py
    └── streamlit_app.py
tests/
├── unit/
├── integration/
└── fixtures/
```

**P2: Brak separacji concerns**

- `app.py` ma 155 linii, ale zawiera:
  - UI rendering (Streamlit)
  - PDF processing (PyMuPDF)
  - Async orchestration
  - Session state management

**P3: Mieszanie async z sync kodem**

```python
# app.py, linia 80-130
async def analyze_all_charts():  # async
    # ...
asyncio.run(analyze_all_charts())  # Wywołanie w sync context
```

To działa, ale jest niebezpieczne w produkcji (event loop conflicts).

---

## 2. KONFIGURACJA

### Kod: `config.py`

### Mocne strony:

- Walidacja zmiennych środowiskowych
- Factory methods dla klientów
- Piękna struktura

### Problemy:

<!-- **P4: load_dotenv() w module scope**
```python
# config.py, linia 7
load_dotenv()  # Wykonuje się przy imporcie
```
Ten sam problem jak w poprzednich projektach, ale mniej krytyczny bo:
- Nie jest w class scope
- Jest tylko jeden call

**Improvement**:
```python
import os
from pathlib import Path
from dotenv import load_dotenv

# Load .env only once
_env_file = Path(__file__).parent / '.env'
if _env_file.exists():
    load_dotenv(_env_file)
else:
    # Try project root
    load_dotenv(Path(__file__).parent.parent / '.env')
``` -->

<!-- **P5: Brak Singleton pattern**
```python
# config.py, linia 29-34
@staticmethod
def get_openai_client():
    return AzureOpenAI(...)  #Nowy client przy każdym wywołaniu
```

**Fix**:
```python
class Config:
    _openai_client = None
    _vision_client = None

    @staticmethod
    def get_openai_client():
        if Config._openai_client is None:
            Config._openai_client = AzureOpenAI(...)
        return Config._openai_client
``` -->

<!-- **P6: Walidacja nie jest używana automatycznie**
```python
# config.py, linia 20-26
@staticmethod
def validate_env_variables():
    # ... validacja
```
To trzeba wywołać ręcznie. Lepiej:
```python
class Config:
    @staticmethod
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        cls.validate_env_variables()
``` -->

<!-- **P7: Hard-coded API version**
```python
# linia 17
OPENAI_API_VERSION = os.getenv('OPENAI_API_VERSION', "2024-02-15-preview")
```
Wersja z lutego 2024 jest stara. Obecna to `2024-08-01-preview` lub nowsza.

--- -->

## 3. CHART ASSISTANT (MAIN LOGIC)

### Kod: `chart_assistant.py`

### ⚠️ Krytyczne problemy:

<!-- **P8: Nieużywany import**
```python
# chart_assistant.py, linia 5
from unittest import result  # WTF? Nieużywany import
```
**Problem**: To sugeruje copy-paste z testów. Dead code. -->

**P9: Magic number - limit 5 plików**

```python
# linia 35
if counter < 5:  # Dlaczego 5? Co się dzieje z resztą?
```

**Problem**:

- Jeśli użytkownik wgra 10 plików, tylko pierwsze 5 zostaną przetworzone
- Brak komunikatu o tym
- Brak dokumentacji dlaczego

**Fix**:

```python
MAX_FILES_TO_PROCESS = 5  # Azure Vision API rate limit

if counter >= MAX_FILES_TO_PROCESS:
    print(f"Warning: Processing limited to {MAX_FILES_TO_PROCESS} files")
    break
```

<!-- **P10: Synchroniczne przetwarzanie plików**
```python
# linia 34-71
for filename, image_bytes in image_bytes_dict.items():
    if counter < 5:
        # ... OCR processing (sync)
```
**Problem**:
- 5 plików × 2-3 sekundy każdy = 10-15 sekund czekania
- OCR requests mogą być równoległe

**Fix**: Użyj `asyncio.gather`:
```python
async def process_single_file(filename, image_bytes):
    image_stream = io.BytesIO(image_bytes)
    read_result = self.vision_client.read_in_stream(image_stream, raw=True)
    operation_id = read_result.headers["Operation-Location"].split("/")[-1]
    result = await self._poll_for_result_async(operation_id)
    return (filename, extract_text(result))

# Process in parallel
tasks = [process_single_file(fn, data) for fn, data in files[:5]]
all_text_results = await asyncio.gather(*tasks)
``` -->

<!-- **P11: Polling blokuje wszystko**
```python
# linia 127-150
def _poll_for_result(self, operation_id, max_attempts=30, poll_interval=1):
    for attempt in range(max_attempts):
        time.sleep(poll_interval)  # ❌ Blocking sleep
```
**Problem**: `time.sleep()` w async context blokuje event loop.

**Fix**:
```python
async def _poll_for_result_async(self, operation_id, max_attempts=30, poll_interval=1):
    for attempt in range(max_attempts):
        # ... check status
        await asyncio.sleep(poll_interval)  # Async sleep
``` -->

<!-- **P12: Brak error handling dla OCR**
```python
# linia 38-41
read_result = self.vision_client.read_in_stream(
    image_stream,
    raw=True
)  # Co jeśli failuje?
```
Azure Vision może zwrócić:
- 400 Bad Request (invalid image)
- 429 Rate Limit
- 500 Internal Server Error

**Fix**:
```python
from azure.core.exceptions import HttpResponseError
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10)
)
def _read_image_with_retry(self, image_stream):
    try:
        return self.vision_client.read_in_stream(image_stream, raw=True)
    except HttpResponseError as e:
        if e.status_code == 429:
            logger.warning("Rate limit hit, retrying...")
            raise  # Let tenacity handle retry
        elif e.status_code == 400:
            raise ValueError(f"Invalid image format: {e}")
        else:
            raise
``` -->

<!-- **P13: Gigantyczny prompt - 400+ tokenów**
```python
# linia 80-96
text = f"""Analyze this chart and create a structured interpretation.

OCR extracted this text (but positions may be jumbled):
{ocr_summary}

For each file please:
1. Identify if there is any chart included and if so, write its title.
2. Identify the chart type (pie chart, bar chart, etc.)
3. Connect each company/label to its correct percentage by looking at the visual layout
4. If it's possible, describe the market share distribution
5. Identify trends
6. Provide insights about the data

And finally, create a concise summary to explain visualize report like: "The chart shows a 15% increase of sales in Q2".
If it's possible provide correlation and dependencies between charts.

Create a clear table showing: Company Name | Market Share %"""
```
**Problem**:
- 15 linii promptu dla każdego wywołania
- Niepotrzebne szczegóły
- Inconsistent instrukcje

**Fix**: Użyj system prompt + krótki user prompt:
```python
system_prompt = """You are a chart analysis expert.
Analyze charts and provide:
1. Chart type
2. Key data points
3. Trends and insights
4. Concise summary"""

user_prompt = f"""Analyze these charts:

OCR Data:
{ocr_summary[:500]}  # Truncate

Return structured analysis."""
``` -->

<!-- **P14: max_tokens=1500 może być za mało**
```python
# linia 122
max_tokens=1500
```
Dla 5 wykresów to może być niewystarczające. GPT może uciąć odpowiedź. -->

<!-- **P15: Brak structured output**
GPT zwraca free text. Lepiej użyć JSON mode:
```python
response = self.openai_client.chat.completions.create(
    model=Config.OPENAI_MODEL,
    messages=messages,
    max_tokens=2000,
    response_format={"type": "json_object"},  # Wymusza JSON
    temperature=0.3  # Dodaj temperature dla consistency
)
``` -->

<!-- **P16: followup_response duplikuje system prompt**
```python
# linia 152-177
def followup_response(self, question, previous_analysis):
    response = self.openai_client.chat.completions.create(
        model=os.getenv("OPENAI_DEPLOYMENT_NAME"),
        messages=[
            {
                "role": "system",
                "content": """You are an expert at analyzing charts and graphs.
                You can see the visual layout and understand which data points connect to which labels.
                Provide structured analysis with correct data associations."""
            },
```
Ten sam system prompt co w `analyze_chart` (linie 113-116).

**Fix**: Wyciągnij do stałej:
```python
SYSTEM_PROMPT = """You are an expert at analyzing charts and graphs..."""

def analyze_chart(self, files):
    # ...
    messages=[{"role": "system", "content": SYSTEM_PROMPT}, ...]

def followup_response(self, question, previous_analysis):
    messages=[{"role": "system", "content": SYSTEM_PROMPT}, ...]
``` -->

---

## 4. STREAMLIT APP

### Kod: `app.py`

### Problemy:

**P17: PDF processing w UI layer**

```python
# app.py, linia 66-75
pdf_bytes = uploaded_file.read()
first_page = fitz.open(stream=pdf_bytes, filetype="pdf")[0]
st.image(first_page.get_pixmap().tobytes("png"), ...)
```

**Problem**: Business logic w presentation layer.

**Fix**: Przenieś do `utils/pdf_processor.py`:

```python
class PDFProcessor:
    @staticmethod
    def get_first_page_preview(pdf_bytes: bytes) -> bytes:
        doc = fitz.open(stream=pdf_bytes, filetype="pdf")
        first_page = doc[0]
        return first_page.get_pixmap().tobytes("png")
```

**P18: Nested async function w sync context**

```python
# linia 80-130
if st.button("🔍 Analyze Charts", type="primary"):

    async def analyze_all_charts():  # Nested async
        # ...

    asyncio.run(analyze_all_charts())  # W Streamlit może crashować
```

**Problem**:

- Streamlit jest sync framework
- `asyncio.run()` tworzy nowy event loop
- Może powodować konflikty

**Lepsze rozwiązanie**:

```python
def analyze_all_charts_sync():
    files = prepare_files(uploaded_files)
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        result = loop.run_until_complete(
            st.session_state.assistant.analyze_chart(files)
        )
        return result
    finally:
        loop.close()
```

**P19: Brak walidacji uploaded files**

```python
# linia 23-28
uploaded_files = st.file_uploader(
    "Choose image files",
    type=["png", "jpg", "jpeg", "pdf"],
    # ... ❌ Brak walidacji rozmiaru
)
```

Użytkownik może wgrać:

- 100 plików naraz
- PDF o rozmiarze 100 MB
- Złośliwy plik

**Fix**:

```python
MAX_FILES = 10
MAX_FILE_SIZE = 20 * 1024 * 1024  # 20MB

if uploaded_files:
    if len(uploaded_files) > MAX_FILES:
        st.error(f"Too many files. Maximum {MAX_FILES} allowed.")
        return

    for file in uploaded_files:
        if file.size > MAX_FILE_SIZE:
            st.error(f"File {file.name} too large (max 20MB)")
            return
```

**P20: St.rerun() bez warunków**

```python
# linia 131
asyncio.run(analyze_all_charts())
st.rerun()  # Zawsze rerun

# linia 155
st.rerun()  # Zawsze rerun
```

**Problem**: Niepotrzebne reruns mogą powodować performance issues.

**P21: Session state bez cleanup**

```python
# linia 9-18
if "assistant" not in st.session_state:
    st.session_state.assistant = ChartsAssistant()
```

`ChartsAssistant` trzyma Azure clients w pamięci przez całą sesję. Jeśli użytkownik nie korzysta przez godzinę, to marnowanie zasobów.

**P22: Brak error boundaries**

```python
# linia 124-128
except Exception as e:
    st.session_state.messages.append({
        "role": "assistant",
        "content": f"Error analyzing chart: {str(e)}"
    })
```

**Problem**: Pokazujesz raw exception user. To może ujawnić:

- API keys (jeśli są w traceback)
- Internal paths
- Azure endpoint URLs

**Fix**:

```python
except HttpResponseError as e:
    st.error("Failed to analyze chart. Please try again.")
    logger.exception(f"Azure API error: {e}")
except Exception as e:
    st.error("An unexpected error occurred.")
    logger.exception(f"Unexpected error: {e}")
```

---

## 5. TESTY

### Mocne strony:

- Folder `tests/` z przypadkami testowymi
- Podział na simple/advanced tests
- Test data w JSON
- Helper utilities

### Problemy:

**P23: Testy nie są pytest**

```python
# tests/simple_tests/run_test_and_validation.py
class TestResultOfAnalysis:
    def _test_chart_analysis(self):  # Nie jest pytest test
        # ...
```

**Problem**:

- Naming convention `_test_*` (z underscore) oznacza private method
- pytest nie wykryje tych testów
- Trzeba uruchamiać ręcznie

**Fix**:

```python
import pytest

class TestChartAnalysis:
    def test_bar_chart_analysis(self):  # pytest wykryje
        # ...

    def test_pie_chart_analysis(self):
        # ...
```

**P24: Testy są integrationowe, nie unit**

```python
# tests/simple_tests/run_test_and_validation.py, linia 29
self.assistant = ChartsAssistant()  # Wywołuje PRAWDZIWE Azure API
```

**Problem**:

- Każdy test = $0.01-0.05 kosztu API
- Wolne (2-3 sekundy/test)
- Zależne od Azure uptime

**Fix**: Mock Azure clients:

```python
from unittest.mock import Mock, patch

@patch('config.Config.get_vision_client')
@patch('config.Config.get_openai_client')
def test_chart_analysis(mock_openai, mock_vision):
    mock_vision.return_value.read_in_stream.return_value = Mock(...)
    mock_openai.return_value.chat.completions.create.return_value = Mock(...)

    assistant = ChartsAssistant()
    result = asyncio.run(assistant.analyze_chart([("test.png", b"...")]))

    assert "chart" in result.lower()
```

**P25: Brak test coverage measurement**
Nie wiadomo ile kodu jest pokryte testami.

**Add**:

```bash
pip install pytest-cov
pytest --cov=. --cov-report=html
```

**P26: Test data commitowane do repo**

```
tests/
├── advanced_charts/  # 5.7 MB!
└── simple_tests/
    └── simple_charts/  # 267 KB
```

**Problem**: 6MB obrazów w git repo = duże repo, wolne clone.

**Fix**:

- Dodaj do `.gitignore`
- Używaj git-lfs dla binary files
- Lub pobieraj test data z Azure Blob Storage

**P27: Niepełne asserty**

```python
# tests/simple_tests/run_test_and_validation.py, linia 36-38
assert "chart type" in analysis_result.lower()
assert "market share" in analysis_result.lower()
assert any(str(i) + "%" for i in range(101) if str(i) in analysis_result)
```

To sprawdza czy JAKIKOLWIEK procent jest w odpowiedzi, nie czy PRAWIDŁOWY.

---

## 6. REQUIREMENTS.TXT

### Problemy:

<!-- **P28: Zbędne pakiety**
```txt
azure-ai-agents  # Nieużywany w projekcie
azure-ai-documentintelligence  # Nieużywany
``` -->
<!--
**P30: Brak dev dependencies**
Projekt ma testy, ale brak:
```txt
# Development
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
black==24.10.0
ruff==0.8.0
``` -->

---

## 7. BEZPIECZEŃSTWO

### Problemy:

**P31: Brak walidacji image content**

```python
# chart_assistant.py, linia 36-40
image_stream = io.BytesIO(image_bytes)
read_result = self.vision_client.read_in_stream(image_stream, raw=True)
```

Użytkownik może przesłać:

- Nie-obraz (np. malformed file)
- Obraz z wulgarną treścią
- Złośliwy plik

**Fix**:

```python
from PIL import Image

def validate_image(image_bytes: bytes):
    try:
        img = Image.open(io.BytesIO(image_bytes))
        img.verify()

        # Check size
        if img.size[0] * img.size[1] > 10000 * 10000:  # 100 megapixels
            raise ValueError("Image too large")

        return True
    except Exception as e:
        raise ValueError(f"Invalid image: {e}")
```

<!-- **P32: API keys mogą wyciekać w error messages**
```python
# app.py, linia 127
content": f"Error analyzing chart: {str(e)}"
```
Jeśli exception zawiera API key w URL (np. w HttpResponseError), zostanie pokazany userowi. -->

**P33: Brak rate limiting**
User może kliknąć "Analyze Charts" 100 razy w minutę.

**Fix**:

```python
import time

if "last_analysis_time" not in st.session_state:
    st.session_state.last_analysis_time = 0

current_time = time.time()
if current_time - st.session_state.last_analysis_time < 5:
    st.error("Please wait 5 seconds between analyses")
    return

st.session_state.last_analysis_time = current_time
```

---

## 8. PERFORMANCE I KOSZTY

### Problemy optymalizacji:

<!-- **P34: Synchroniczne przetwarzanie = wolne**
```python
# chart_assistant.py, linia 34-71
for filename, image_bytes in image_bytes_dict.items():
    # Sequential processing
```
5 plików × 3 sekundy = 15 sekund.

Z async: 5 plików × 3 sekundy = ~3 sekundy (parallel). -->

<!-- **P35: Gigantyczne prompty = wysokie koszty**
```python
# Obecny prompt: ~400 tokenów
# GPT-4 Vision: $0.01 per 1k tokens
# 1000 analiz/dzień = $4/dzień = $120/miesiąc
```

**Po optymalizacji**:
```python
# Krótszy prompt: ~100 tokenów
# 1000 analiz/dzień = $1/dzień = $30/miesiąc
# Oszczędność: $90/miesiąc (75%)
``` -->

**P36: Brak cache dla powtarzających się obrazów**
Jeśli 10 userów analizuje ten sam wykres, robisz 10 identycznych API calls.

**Fix**:

```python
import hashlib
from functools import lru_cache

@lru_cache(maxsize=100)
def analyze_chart_cached(image_hash: str, image_bytes: bytes):
    # ...

def get_image_hash(image_bytes: bytes) -> str:
    return hashlib.md5(image_bytes).hexdigest()
```

**P37: PDF conversion w pamięci**

```python
# app.py, linia 99-100
pix = page.get_pixmap()
img_bytes = pix.tobytes("jpg")
```

100-stronicowy PDF = 100 × 5MB = 500MB w RAM.

**Fix**: Process w chunkach:

```python
MAX_PAGES = 20

for page_num, page in enumerate(doc):
    if page_num >= MAX_PAGES:
        st.warning(f"Processing first {MAX_PAGES} pages only")
        break
    # ...
```

---

## 9. DOKUMENTACJA

### ✅ Mocne strony:

- README petarda
- Struktura projektu opisana
- Instrukcje uruchomienia
- Linki do demo (Google Drive)
- Wyjaśnienie test cases

### ⚠️ Braki:

<!-- **P38: Brak .env.example**
```bash
# .env.example
VISION_ENDPOINT=https://your-vision.cognitiveservices.azure.com/
VISION_KEY=your_key_here
OPENAI_ENDPOINT=https://your-openai.openai.azure.com/
OPENAI_KEY=your_key_here
OPENAI_DEPLOYMENT_NAME=gpt-4-vision
OPENAI_API_VERSION=2024-02-15-preview
``` -->

**P39: Brak API documentation**

```python
async def analyze_chart(self, files):
    """Computer Vision OCR + GPT-4 Vision to analyze chart images and extract structured data."""
```

Docstring jest OK, ale brak:

- Parametrów
- Return type
- Przykładów użycia

**P40: Brak architecture diagram**
README pokazuje strukturę folderów, ale brak diagramu przepływu:

```
User uploads image/PDF
    ↓
Streamlit UI (app.py)
    ↓
PDF → Convert pages to images (PyMuPDF)
    ↓
ChartsAssistant.analyze_chart()
    ↓
├─→ Azure Computer Vision (OCR)
│   ↓
│   Text extraction (async)
│
└─→ GPT-4 Vision
    ↓
    Chart analysis + insights
    ↓
    Return to user
```

---

## 10. CODE QUALITY

### Problemy:

**P41: Brak type hints**

```python
# chart_assistant.py, linia 15
async def analyze_chart(self, files):  # Brak type hints
```

**Powinno być**:

```python
from typing import List, Tuple

async def analyze_chart(
    self,
    files: List[Tuple[str, bytes]]
) -> str:
```

**P42: Inconsistent naming**

```python
# app.py
uploaded_files  # snake_case
# chart_assistant.py
image_bytes_dict  # snake_cas
base64_images_dict  # snake_cas
all_text_results  # snake_case
```

Actually, naming jest spójny! To jest PLUS.

<!-- **P43: Magic strings**
```python
# app.py, linia 23-28
type=["png", "jpg", "jpeg", "pdf"]

# chart_assistant.py, linia 94
ext = filename.lower().split(".")[-1]
if ext == "pdf":
```
**Fix**:
```python
ALLOWED_IMAGE_FORMATS = ["png", "jpg", "jpeg"]
ALLOWED_PDF_FORMAT = ["pdf"]
ALLOWED_FORMATS = ALLOWED_IMAGE_FORMATS + ALLOWED_PDF_FORMAT
``` -->

**P44: Długie funkcje**

```python
# app.py, linia 80-131 - 51 linii
async def analyze_all_charts():
```

**Fix**: Podziel na mniejsze funkcje:

```python
def prepare_files(uploaded_files):
    # ...

def convert_pdf_to_images(files):
    # ...

async def analyze_and_update_messages(files):
    # ...
```

---

## PODSUMOWANIE

### Krytyczne problemy (MUST FIX):

1. **P9**: Magic number - limit 5 plików bez ostrzeżenia
<!-- 2. **P11**: Blocking `time.sleep()` w async context -->
2. **P19**: Brak walidacji uploaded files (security)
3. **P24**: Testy używają prawdziwego Azure API (koszty)
   <!-- 5. **P28**: Brak pinned dependencies -->
   <!-- 6. **P32**: API keys mogą wyciekać w error messages -->

### Wysokie priorytety (powinny być fixowane):

7. **P10**: Synchroniczne przetwarzanie plików (performance)
8. **P13**: Gigantyczny prompt (koszty $90/miesiąc możliwe do zaoszczędzenia)
9. **P18**: Nested async w sync context (może crashować)
10. **P23**: Testy nie są pytest-compatible
11. **P35**: Wysokie koszty API
12. **P41**: Brak type hints

### Nice-to-have (długoterminowe):

13. **P1**: Lepsza struktura pakietu
14. **P5**: Singleton pattern dla Azure clients
15. **P36**: Cache dla powtarzających się obrazów

---

## OCENA KOŃCOWA

**Ogólna ocena: 8/10**
