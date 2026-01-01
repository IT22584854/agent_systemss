import re

def load_markdown_corpus(path: str) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        text = f.read()

    blocks = re.split(r"\n---\n", text)
    dataset = []

    for block in blocks:
        q = re.search(r"### Question\n(.+?)\n\n", block, re.S)
        a = re.search(r"### Answer\n(.+?)\n\n", block, re.S)
        c = re.search(r"## (.+)", block)

        if q and a:
            dataset.append({
                "category": c.group(1).strip() if c else "general_health",
                "question": q.group(1).strip(),
                "answer": a.group(1).strip()
            })

    return dataset
