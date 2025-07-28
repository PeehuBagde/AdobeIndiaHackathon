import os
import re
import json
from pdfminer.high_level import extract_pages
from pdfminer.layout import LTTextContainer

input_dir = "input"
output_dir = "output"

# ✅ Extracts the most likely title (first long block of text on the first page)
def extract_title(pdf_path):
    for page_layout in extract_pages(pdf_path):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                text = element.get_text().strip()
                if len(text.split()) >= 5 and len(text) <= 120:
                    return text
    return "Untitled Document"

# ✅ Extracts only meaningful headings, skips form-style fields
def extract_headings(pdf_path):
    outline = []
    heading_candidates = []

    for page_number, page_layout in enumerate(extract_pages(pdf_path), start=1):
        for element in page_layout:
            if isinstance(element, LTTextContainer):
                lines = element.get_text().split("\n")
                for line in lines:
                    text = line.strip()

                    # ❌ Skip common form words and short junk
                    if text.lower() in {
                        "name", "age", "date", "s.no", "relationship",
                        "designation", "rs.", "i declare", "amount of advance required.",
                        "service", "pay + si + npa", "signature of government servant."
                    }:
                        continue

                    # ❌ Skip lines that are just numbers or very short
                    if re.fullmatch(r"\d{1,2}\.?", text):
                        continue
                    if len(text.split()) < 4:
                        continue
                    if re.match(r"^\d+\.\s*[A-Za-z ]{0,10}$", text):  # e.g., "3. Age"
                        continue

                    # ✅ Accept as heading
                    heading = {
                        "level": "H1",
                        "text": text,
                        "page": page_number
                    }
                    heading_candidates.append(heading)

    # ❌ If they all start with numbers but no real content, treat as form — skip
    if all(h["text"].strip().split()[0].rstrip(".").isdigit() for h in heading_candidates):
        return []

    return heading_candidates

def main():
    os.makedirs(output_dir, exist_ok=True)

    for filename in os.listdir(input_dir):
        if filename.lower().endswith(".pdf"):
            pdf_path = os.path.join(input_dir, filename)

            title = extract_title(pdf_path)
            headings = extract_headings(pdf_path)

            # Clean text
            title = title.strip()
            for h in headings:
                h["text"] = h["text"].strip()

            output = {
                "title": title,
                "outline": headings
            }

            out_path = os.path.join(output_dir, filename.replace(".pdf", ".json"))
            with open(out_path, "w", encoding="utf-8") as f:
                json.dump(output, f, indent=2, ensure_ascii=False)

            print(f"✅ Output written: {out_path}")

if __name__ == "__main__":
    main()
