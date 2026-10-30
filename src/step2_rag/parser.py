"""Markdown and Catalog Parser for ZentroMart Knowledge Base."""
import csv
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from src.config import KB_DIR, DATA_DIR


def parse_frontmatter(text: str) -> tuple[Dict[str, Any], str]:
    """Parse YAML-style frontmatter from markdown text."""
    metadata = {}
    body = text
    if text.startswith("---"):
        parts = text.split("---", 2)
        if len(parts) >= 3:
            fm_text = parts[1]
            body = parts[2].strip()
            for line in fm_text.strip().split("\n"):
                if ":" in line:
                    key, val = line.split(":", 1)
                    metadata[key.strip()] = val.strip()
    return metadata, body


def parse_kb_documents(kb_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Parse all 21 markdown documents in kb_dir into structured chunks with section IDs."""
    target_dir = kb_dir or KB_DIR
    chunks = []

    for file_path in sorted(target_dir.glob("*.md")):
        text = file_path.read_text(encoding="utf-8")
        metadata, body = parse_frontmatter(text)

        doc_id = metadata.get("doc_id", file_path.stem)
        doc_type = metadata.get("doc_type", "policy")
        status = metadata.get("status", "current")
        effective_from = metadata.get("effective_from", "")
        title = metadata.get("title", file_path.stem)
        language = metadata.get("language", "en")

        # Split body into sections by ## [SECTION_ID] Heading
        section_pattern = re.compile(r"^##\s*\[([^\]]+)\]\s*(.*)$", re.M)
        matches = list(section_pattern.finditer(body))

        if not matches:
            # Whole document as a chunk
            chunk = {
                "chunk_id": doc_id,
                "section_id": doc_id,
                "section_title": title,
                "doc_id": doc_id,
                "doc_title": title,
                "doc_type": doc_type,
                "status": status,
                "effective_from": effective_from,
                "language": language,
                "file_name": file_path.name,
                "content": body,
                "source": f"kb/{file_path.name}"
            }
            chunks.append(chunk)
            continue

        for i, match in enumerate(matches):
            sec_id = match.group(1).strip()
            sec_title = match.group(2).strip()
            start_pos = match.end()
            end_pos = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            sec_body = body[start_pos:end_pos].strip()

            full_chunk_text = f"## [{sec_id}] {sec_title}\n{sec_body}"

            chunk = {
                "chunk_id": f"{doc_id}::{sec_id}",
                "section_id": sec_id,
                "section_title": sec_title,
                "doc_id": doc_id,
                "doc_title": title,
                "doc_type": doc_type,
                "status": status,
                "effective_from": effective_from,
                "language": language,
                "file_name": file_path.name,
                "content": full_chunk_text,
                "source": f"kb/{file_path.name}"
            }
            chunks.append(chunk)

    return chunks


def parse_products_catalog(data_dir: Optional[Path] = None) -> List[Dict[str, Any]]:
    """Parse products.csv so product details can be cited as products.csv:<SKU>."""
    target_dir = data_dir or DATA_DIR
    products_file = target_dir / "products.csv"
    product_chunks = []

    if not products_file.exists():
        return product_chunks

    with open(products_file, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            sku = row["sku"].strip()
            title = row["title"].strip()
            brand = row["brand"].strip()
            category = row["return_category"].strip()
            price = row["price_inr"].strip()
            fulfilled_by = row["fulfilled_by"].strip()
            assured = row["assured"].strip()
            warranty_months = row["warranty_months"].strip()
            desc = row["description"].strip()

            text = (
                f"Product SKU: {sku}\n"
                f"Title: {title}\n"
                f"Brand: {brand}\n"
                f"Return Category: {category}\n"
                f"Price: ₹{price}\n"
                f"Fulfilled By: {fulfilled_by}\n"
                f"Assured Badge: {assured}\n"
                f"Brand Warranty: {warranty_months} months\n"
                f"Description: {desc}"
            )

            product_chunks.append({
                "chunk_id": f"products.csv:{sku}",
                "section_id": f"products.csv:{sku}",
                "section_title": f"{sku} - {title}",
                "doc_id": "products.csv",
                "doc_title": "Product Catalog",
                "doc_type": "catalog",
                "status": "current",
                "effective_from": "2026-01-01",
                "language": "en",
                "file_name": "products.csv",
                "content": text,
                "source": f"data/products.csv:{sku}",
                "sku": sku,
                "title": title,
                "brand": brand,
                "price_inr": price,
                "category": category,
                "return_category": category,
                "fulfilled_by": fulfilled_by,
                "assured": assured.lower() == "true",
                "warranty_months": warranty_months
            })

    return product_chunks
