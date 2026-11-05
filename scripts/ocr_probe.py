#!/usr/bin/env python3
"""Read-only OCR probe for one public Almere NotuBiz PDF page.

No OCR text, rendered images, or downloaded documents are uploaded to GitHub.
Only aggregate statistics are printed for inspection.
"""
import argparse
import csv
import io
import json
import os
import statistics
import subprocess
import tempfile
import urllib.request
import urllib.error
from pathlib import Path

PROXY_URL = "https://yfnxuhuxdagomklpgswh.supabase.co/functions/v1/ocr-github-oidc-pdf-probe-v1?document_id=28301"
OIDC_AUDIENCE = "almere-ocr-supabase-pdf-v1"
MAX_PDF_BYTES = 40_000_000


def run(*args, timeout=600):
    return subprocess.run(args, check=True, capture_output=True, text=True, timeout=timeout)


def download_pdf(destination):
    token_request_url = os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    token_request_secret = os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]
    from urllib.parse import urlencode
    separator = "&" if "?" in token_request_url else "?"
    oidc_request = urllib.request.Request(
        token_request_url + separator + urlencode({"audience": OIDC_AUDIENCE}),
        headers={"Authorization": "Bearer " + token_request_secret},
    )
    with urllib.request.urlopen(oidc_request, timeout=20) as oidc_response:
        oidc_token = json.load(oidc_response)["value"]
    request = urllib.request.Request(
        PROXY_URL,
        headers={
            "Accept": "application/pdf",
            "Authorization": "Bearer " + oidc_token,
        },
    )
    try:
        response_context = urllib.request.urlopen(request, timeout=90)
    except urllib.error.HTTPError as exc:
        # The proxy returns a short machine-readable error code, not the PDF.
        detail = exc.read(1000).decode("utf-8", errors="replace")
        raise RuntimeError(f"Supabase PDF proxy HTTP {exc.code}: {detail}") from None
    with response_context as response:
        declared = int(response.headers.get("Content-Length", "0"))
        if declared > MAX_PDF_BYTES:
            raise ValueError("Document exceeds download limit")
        with destination.open("wb") as f:
            total = 0
            while True:
                chunk = response.read(65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > MAX_PDF_BYTES:
                    raise ValueError("Document exceeds download limit")
                f.write(chunk)
    with destination.open("rb") as f:
        if f.read(5) != b"%PDF-":
            raise ValueError("Source did not return a PDF")
    return total, oidc_token


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--page", type=int, default=387)
    parser.add_argument("--dpi", type=int, choices=(200, 250, 300, 350), default=300)
    args = parser.parse_args()
    if not 1 <= args.page <= 1000:
        parser.error("Page must be between 1 and 1000")

    with tempfile.TemporaryDirectory(prefix="almere_ocr_") as temporary:
        folder = Path(temporary)
        pdf = folder / "source.pdf"
        source_bytes, oidc_token = download_pdf(pdf)
        info = run("pdfinfo", str(pdf), timeout=90).stdout
        pages = int(next(line.split(":", 1)[1].strip() for line in info.splitlines() if line.startswith("Pages:")))
        if args.page > pages:
            parser.error(f"Page {args.page} exceeds the PDF page count {pages}")

        image_prefix = folder / "page"
        run(
            "pdftoppm", "-f", str(args.page), "-l", str(args.page),
            "-r", str(args.dpi), "-singlefile", "-gray",
            "-png", str(pdf), str(image_prefix), timeout=600,
        )
        image = folder / "page.png"
        tsv = run("tesseract", str(image), "stdout", "-l", "nld+eng", "--psm", "3", "tsv", timeout=600).stdout
        rows = list(csv.DictReader(io.StringIO(tsv), delimiter="\t"))
        words = [r for r in rows if r["level"] == "5" and r["text"].strip()]
        confidence = [float(r["conf"]) for r in words if float(r["conf"]) >= 0]
        report = {
            "document_id": 28301,
            "page": args.page,
            "total_pages": pages,
            "dpi": args.dpi,
            "pdf_bytes": source_bytes,
            "image_bytes": image.stat().st_size,
            "recognized_words": len(words),
            "recognized_characters": sum(len(r["text"]) for r in words),
            "mean_word_confidence": round(statistics.mean(confidence), 1) if confidence else None,
            "median_word_confidence": round(statistics.median(confidence), 1) if confidence else None,
            "words_confidence_below_50": sum(c < 50 for c in confidence),
            "status": "completed",
            "note": "Statistics are not an independent OCR accuracy benchmark.",
        }
        # Save OCR text only in private Supabase Storage, never in public GitHub logs.
        lines = {}
        for word in words:
            key = (word["block_num"], word["par_num"], word["line_num"])
            lines.setdefault(key, []).append(word["text"])
        recognized_text = "\\n".join(" ".join(line) for line in lines.values())
        payload = {
            "document_id": 28301, "page": args.page, "dpi": args.dpi,
            "engine": "tesseract-nld-eng", "text": recognized_text,
            "statistics": report,
        }
        if args.page == 387 and args.dpi == 300:
            upload_request = urllib.request.Request(
                PROXY_URL,
                data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
                headers={"Authorization": "Bearer " + oidc_token, "Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(upload_request, timeout=45) as upload_response:
                    upload_result = json.load(upload_response)
            except urllib.error.HTTPError as exc:
                raise RuntimeError(f"OCR result upload failed HTTP {exc.code}: "
                                   + exc.read(500).decode("utf-8", errors="replace")) from None
            report["storage_write"] = upload_result.get("ok")
            report["storage_path"] = upload_result.get("storage_path")
        print(json.dumps(report, ensure_ascii=False, indent=2))
        summary = os.environ.get("GITHUB_STEP_SUMMARY")
        if summary:
            with open(summary, "a", encoding="utf-8") as output:
                output.write("## OCR proefmeting\n\n")
                output.write("| Kenmerk | Resultaat |\n|---|---:|\n")
                for key, value in report.items():
                    output.write(f"| {key} | {value} |\n")
                output.write("\nGeen documentinhoud of OCR tekst gepubliceerd.\n")


if __name__ == "__main__":
    main()
