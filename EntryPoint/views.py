from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from .ocr_service import analyze_label_image


# -----------------------------
# BASIC PAGES
# -----------------------------
def splash(request):
    return render(request, "splash.html")


def main(request):
    return render(request, "main.html")


@require_POST
def analyze_ocr_label(request):
    image_file = request.FILES.get("image")
    if not image_file:
        return JsonResponse({"status": "error", "message": "Image file is required."}, status=400)

    try:
        ocr_data = analyze_label_image(image_file=image_file)
    except ValueError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)
    except RuntimeError as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=502)
    except Exception as exc:
        return JsonResponse({"status": "error", "message": str(exc)}, status=500)

    return JsonResponse(
    {
        "status": "success",
        "ingredients": ocr_data.get("ingredients", []),  # ✅ keep as list, frontend joins it
        "ocr_text": ocr_data.get("raw_text", ""),
        "ocr_nutrients": ocr_data.get("nutrients", []),
        "nutrition_per_100g": ocr_data.get("nutrition_per_100g", {}),  # ✅ was "nutrition"
        "product_name": "OCR Label Analysis",
        "brand": "Extracted from uploaded label",
        "expiry": {
            "status": "OCR Only",
            "message": "No barcode lookup used in this mode.",
        },
        "quality": {
            "quality": "OCR Extraction",
            "score": "-",
            "message": "Chart generated from OCR-detected values.",
        },
        "image": None,
    }
)
# ✅ Add this so unexpected errors don't return None
