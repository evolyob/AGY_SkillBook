# Existing PDF Processing & Edit Reference (`pdf_process.md`)

Covers Input-oriented PDF operations: text/table extraction, OCR, page manipulation, form filling, and batch processing.

## 1. Text & Table Extraction
```python
import pdfplumber, pandas as pd
# Extract Text
with pdfplumber.open("input.pdf") as pdf:
    text = "\n".join(page.extract_text() or "" for page in pdf.pages)

# Extract Tables to DataFrame / Excel
with pdfplumber.open("input.pdf") as pdf:
    tables = [pd.DataFrame(t[1:], columns=t[0]) for page in pdf.pages for t in page.extract_tables() if t]
    if tables: pd.concat(tables, ignore_index=True).to_excel("extracted_tables.xlsx", index=False)
```
```bash
# Fast CLI Layout Text Extraction
pdftotext -layout input.pdf output.txt
pdftotext -f 1 -l 5 input.pdf pages_1_5.txt
```

## 2. OCR for Scanned PDFs & Asset Extraction
```python
import pytesseract
from pdf2image import convert_from_path

images = convert_from_path("scanned.pdf")
full_text = "\n\n".join(f"--- Page {i+1} ---\n{pytesseract.image_to_string(img, lang='chi_tra+eng')}" for i, img in enumerate(images))
with open("ocr_output.txt", "w", encoding="utf-8") as f: f.write(full_text)
```
```bash
# Extract all embedded images
pdfimages -png -j input.pdf image_prefix
```

## 3. Page Manipulation: Merge, Split, Rotate, Encrypt
```python
from pypdf import PdfReader, PdfWriter

# Merge
writer = PdfWriter()
for f in ["doc1.pdf", "doc2.pdf"]: writer.append(f)
with open("merged.pdf", "wb") as out: writer.write(out)

# Split / Rotate / Encrypt
reader = PdfReader("input.pdf")
writer = PdfWriter()
for page in reader.pages:
    page.rotate(90)
    writer.add_page(page)
writer.encrypt("userpass", "ownerpass")
with open("processed.pdf", "wb") as out: writer.write(out)
```
```bash
# CLI Manipulation with qpdf
qpdf --empty --pages file1.pdf file2.pdf -- merged.pdf
qpdf input.pdf --pages . 1-5 -- pages1-5.pdf
qpdf input.pdf output_repaired.pdf
```

## 4. Form Filling & Large PDF Chunking
```python
from pypdf import PdfReader, PdfWriter

# Form Filling
reader = PdfReader("form.pdf")
writer = PdfWriter()
writer.append(reader)
writer.update_page_form_field_values(writer.pages[0], {"name": "John", "status": "Approved"})
with open("filled.pdf", "wb") as out: writer.write(out)

# Large PDF Chunking (500 pages per chunk)
reader = PdfReader("huge.pdf")
for start in range(0, len(reader.pages), 500):
    w = PdfWriter()
    for p in reader.pages[start:start+500]: w.add_page(p)
    with open(f"chunk_{start//500 + 1}.pdf", "wb") as out: w.write(out)
```

