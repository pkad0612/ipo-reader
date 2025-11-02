import pdfplumber
import subprocess
import tempfile
import os

# Try importing OCR libs; if unavailable, set flag
try:
    import pytesseract
    from PIL import Image
    OCR_AVAILABLE = True
except ImportError:
    OCR_AVAILABLE = False

def extract_text_from_pdf(pdf_path: str):
    pages_text = []
    with pdfplumber.open(pdf_path) as pdf:
        for i, page in enumerate(pdf.pages):
            text = (page.extract_text() or "").strip()
            # Only OCR if library is available and page has too little text
            if len(text) < 50 and OCR_AVAILABLE:
                text = ocr_page(pdf_path, i)
            pages_text.append(text)
    return pages_text

def ocr_page(pdf_path: str, page_index: int) -> str:
    if not OCR_AVAILABLE:
        return ""
    with tempfile.TemporaryDirectory() as td:
        img_prefix = os.path.join(td, "page")
        subprocess.run(
            ["pdftoppm", pdf_path, img_prefix, "-png",
             "-f", str(page_index+1), "-l", str(page_index+1)],
            check=True
        )
        img_path = img_prefix + "-1.png"
        image = Image.open(img_path)
        return pytesseract.image_to_string(image).strip()
