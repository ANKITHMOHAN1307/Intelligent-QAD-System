import base64
import json
import os
import re
from urllib import error, request as urllib_request

OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _safe_float(value):
    try:
        if value is None:
            return None
        if isinstance(value, (int, float)):
            return float(value)
        cleaned = re.sub(r"[^0-9.\-]", "", str(value))
        if not cleaned:
            return None
        return float(cleaned)
    except (ValueError, TypeError):
        return None


def _normalize_nutrients_per_100g(nutrients):
    normalized = {}
    for item in nutrients or []:
        name = str(item.get("name", "")).strip()
        value = _safe_float(item.get("value"))
        unit = str(item.get("unit", "")).strip().lower() or "g"
        basis = str(item.get("basis", "100g")).strip().lower()

        if not name:
            continue

        if value is None:
            normalized[name] = {
                "value_per_100g": None,
                "unit": unit,
                "source_basis": basis,
            }
            continue

        if basis == "100g":
            value_per_100g = value
        elif basis.endswith("g"):
            basis_num = _safe_float(basis.replace("g", ""))
            value_per_100g = (value / basis_num) * 100 if basis_num and basis_num > 0 else value
        elif basis.endswith("ml"):
            basis_num = _safe_float(basis.replace("ml", ""))
            value_per_100g = (value / basis_num) * 100 if basis_num and basis_num > 0 else value
        else:
            value_per_100g = value

        normalized[name] = {
            "value_per_100g": round(value_per_100g, 3) if value_per_100g is not None else None,
            "unit": unit,
            "source_basis": basis,
        }

    return normalized


def _extract_json(raw_text):
    if not raw_text:
        return None

    text = raw_text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    match = re.search(r"\{[\s\S]*\}", text)
    if not match:
        return None

    try:
        return json.loads(match.group(0))
    except json.JSONDecodeError:
        return None


def analyze_label_image(image_base64, mime_type="image/jpeg"):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not configured.")

    data_url = f"data:{mime_type};base64,{image_base64}"

    prompt = (
        "Read this product label image. Extract OCR text and identify key food-label fields. "
        "Return strict JSON with keys: raw_text, ingredients (array of strings), "
        "nutrients (array of objects with name,value,unit,basis). "
        "For basis use values like 100g, 30g, 100ml, etc. "
        "If missing, use nulls and empty arrays. No markdown."
    )

    payload = {
        "model": OPENAI_MODEL,
        "temperature": 0.1,
        "messages": [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": data_url}},
                ],
            }
        ],
        "response_format": {"type": "json_object"},
    }

    req = urllib_request.Request(
        OPENAI_API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )

    try:
        with urllib_request.urlopen(req, timeout=45) as response:
            raw = json.loads(response.read().decode("utf-8"))
    except (error.HTTPError, error.URLError, TimeoutError) as exc:
        raise RuntimeError("Unable to contact AI OCR service.") from exc

    choices = raw.get("choices") or []
    if not choices:
        raise RuntimeError("AI OCR service returned no choices.")

    message_content = choices[0].get("message", {}).get("content", "")
    parsed = _extract_json(message_content)
    if not parsed:
        raise RuntimeError("AI OCR service returned invalid JSON payload.")

    nutrients = parsed.get("nutrients") or []

    return {
        "raw_text": parsed.get("raw_text") or "",
        "ingredients": parsed.get("ingredients") or [],
        "nutrients": nutrients,
        "nutrition_per_100g": _normalize_nutrients_per_100g(nutrients),
    }


def image_file_to_base64(file_obj):
    binary = file_obj.read()
    return base64.b64encode(binary).decode("utf-8")
