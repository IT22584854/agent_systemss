import os
from docling.document_converter import DocumentConverter

# We only want the high-value targets that are likely incomplete
targets = [
    "MOH_Mental-Health-Service-Providers-Directory-2023.pdf",
    "MOH_Digital-Health-Blue-Print-Full-Book-01.11.2023-Final.pdf"
]

converter = DocumentConverter() # CPU Mode
output_dir = "0_raw_data/markdown"

for target in targets:
    pdf_path = f"0_raw_data/pdfs/{target}"
    if os.path.exists(pdf_path):
        print(f"🚀 Deep-processing: {target}...")
        try:
            result = converter.convert(pdf_path)
            with open(f"{output_dir}/{target.replace('.pdf', '.md')}", "w", encoding="utf-8") as f:
                f.write(result.document.export_to_markdown())
            print(f"✅ Success!")
        except Exception as e:
            print(f"❌ Failed: {e}")