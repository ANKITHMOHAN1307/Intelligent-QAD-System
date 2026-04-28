# Intelligent-QAD-System

Intelligent-QAD-System is a Django web application that analyzes packaged food labels using a **barcode-first** approach with an **OCR fallback pipeline**.

The app tries to decode a barcode and fetch product metadata from Open Food Facts. If barcode lookup fails, it sends the uploaded label image through OCR.Space, then uses an LLM-assisted parser (Groq) plus regex fallback logic to extract ingredients and nutrition.

---

## Core Workflow

1. User opens splash page (`/`) and is redirected to the main analyzer UI (`/main/`).
2. User either:
   - scans barcode using live camera, or
   - uploads a barcode image.
3. Frontend decodes barcode with QuaggaJS.
4. Backend endpoint `/analyze-barcode/` queries Open Food Facts for product data.
5. If barcode path fails (missing barcode, API/network issue, no product), app falls back to OCR mode.
6. OCR mode posts image to `/analyze-ocr-label/`:
   - image is sent to OCR.Space,
   - text is parsed by Groq model into structured JSON,
   - regex extraction is used if LLM output is invalid.
7. UI renders:
   - ingredients,
   - ingredient classification (organic / chemical / additive),
   - nutrition chart,
   - raw OCR text,
   - quality + expiry status badges.

---

## Features

- **Barcode-first product analysis** via Open Food Facts API.
- **OCR fallback** for labels where barcode fails or is unavailable.
- **Structured nutrient normalization** to per-100g values.
- **Nutrition quality scoring** from sugar/salt/fat heuristics.
- **Expiry-state estimation** based on parsed expiration date.
- **Ingredient category grouping** in UI (organic, chemical, additive).
- **Asynchronous fallback task support** using Celery.

---

## Tech Stack

- **Backend:** Django, Celery, django-celery-results
- **OCR:** OCR.Space API
- **LLM parsing:** Groq (`llama-3.3-70b-versatile`)
- **Frontend:** Django templates + vanilla JavaScript
- **Client-side barcode decode:** QuaggaJS
- **Visualization:** Chart.js
- **Broker / result backend:** Redis
- **Containerization:** Docker + Gunicorn

---

## Project Structure

```text
Intelligent-QAD-System/
├── MainFolder/                 # Django project config (settings, urls, celery)
├── EntryPoint/                 # Main app (views, OCR service, templates, tasks)
│   ├── templates/
│   │   ├── splash.html
│   │   ├── main.html
│   │   └── master.html
│   ├── views.py                # API + page endpoints
│   ├── ocr_service.py          # OCR + LLM + regex fallback pipeline
│   └── tasks.py                # Celery fallback task
├── manage.py
├── Dockerfile
├── docker-compose.yml
├── Pipfile
└── README.md
```

---

## Endpoints

- `GET /` → Splash page
- `GET /main/` → Main analyzer page
- `POST /analyze-barcode/` → Barcode lookup + nutrition/quality response
- `POST /analyze-ocr-label/` → OCR + parsed nutrition response
- `GET /task-status/<task_id>/` → Celery task status

---

## Environment Variables

Minimum required for full functionality:

- `OCR_SPACE_API_KEY` (required for OCR mode)
- `GROQ_API_KEY` (required for LLM nutrient extraction)

Optional / infra-related:

- `DB_ENGINE`, `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- `CELERY_BROKER_URL` (default: `redis://127.0.0.1:6379/0`)
- `CELERY_RESULT_BACKEND` (default: `redis://127.0.0.1:6379/0`)

---

## Local Setup

### 1) Create virtual environment and install dependencies

Using Pipenv:

```bash
pip install pipenv
pipenv install
pipenv shell
```

### 2) Configure environment

Create `.env` in project root and add:

```env
OCR_SPACE_API_KEY=your_ocr_space_key
GROQ_API_KEY=your_groq_key
```

### 3) Apply migrations

```bash
python manage.py migrate
```

### 4) Run Django server

```bash
python manage.py runserver
```

Open: `http://127.0.0.1:8000/`

---

## Running Celery (optional but recommended)

In another terminal:

```bash
celery -A MainFolder worker -l info
```

If you use async fallback paths, make sure Redis is running and matches `CELERY_BROKER_URL`.

---

## Docker

Build and run:

```bash
docker compose up --build
```

The container runs migrations and starts Gunicorn on port `8000`.

---

## Notes

- OCR quality depends on image clarity, orientation, and lighting.
- Open Food Facts coverage varies by product/region; fallback is expected for missing records.
- Current nutrition quality score is heuristic, meant for quick screening (not clinical advice).

---

## License


No license file is currently included in this repository.