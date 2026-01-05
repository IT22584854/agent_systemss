from docling.document_converter import DocumentConverter
import os
import gc
import traceback

INPUT_DIR = "0_raw_data/pdfs"
OUTPUT_DIR = "0_raw_data/markdown"
FAILED_LOG = "failed_pdfs.txt"


def process_to_markdown():
    converter = DocumentConverter()

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    pdfs = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    total = len(pdfs)

    print(f"Found {total} PDFs\n")

    for idx, filename in enumerate(pdfs, start=1):
        pdf_path = os.path.join(INPUT_DIR, filename)
        output_filename = filename.replace(".pdf", ".md")
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        # Skip already processed PDFs
        if os.path.exists(output_path):
            print(f"[{idx}/{total}] Skipping (already done): {filename}")
            continue

        print(f"[{idx}/{total}] Processing: {filename}")

        try:
            result = converter.convert(pdf_path)
            markdown_output = result.document.export_to_markdown()

            with open(output_path, "w", encoding="utf-8") as f:
                f.write(markdown_output)

            print(f"[{idx}/{total}] ✅ Done: {output_filename}")

        except Exception as e:
            print(f"[{idx}/{total}] ❌ FAILED: {filename}")
            print(str(e))

            # Log failure for later review
            with open(FAILED_LOG, "a", encoding="utf-8") as log:
                log.write(f"{filename}\n")
                log.write(traceback.format_exc())
                log.write("\n" + "-" * 80 + "\n")

        finally:
            # Aggressively free memory between PDFs
            gc.collect()

    print("\nProcessing complete.")
    print(f"Check '{FAILED_LOG}' for any failures.")


if __name__ == "__main__":
    process_to_markdown()
