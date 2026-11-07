#!/usr/bin/env python3
"""Private OCR audit: compare GitHub Tesseract results with embedded PDF text.
Never print source text or OCR text to logs."""
import difflib
import io
import json
import re
import subprocess
import tempfile
from pathlib import Path
from ocr_queue_worker import oidc_token, post

def norm(text):
    return re.sub(r"\\s+", " ", text).strip()

def main():
    token=oidc_token()
    source=post(token,{"action":"audit_source","document_id":28301,"page":386},pdf=True)
    if not source.startswith(b"%PDF-"):raise ValueError("Not a PDF")
    with tempfile.TemporaryDirectory() as tmp:
        path=Path(tmp)/"source.pdf"
        path.write_bytes(source)
        results=[]
        for page in (386,387,388):
            ocr=json.loads(post(token,{"action":"audit_read","document_id":28301,"page":page}))
            text=ocr.get("text")
            if not isinstance(text,str) or not text.strip():raise ValueError(f"Missing OCR text for {page}")
            original=subprocess.run(["pdftotext","-f",str(page),"-l",str(page),"-layout",str(path),"-"],capture_output=True,text=True,check=True).stdout
            a,b=norm(original),norm(text)
            if not a:raise ValueError(f"No embedded PDF text for {page}")
            ratio=difflib.SequenceMatcher(None,a,b,autojunk=False).ratio()
            words_a,words_b=len(a.split()),len(b.split())
            result={"page":page,"pdf_words":words_a,"ocr_words":words_b,"similarity":round(ratio,5),"exact_match":a==b}
            results.append(result)
            print(json.dumps(result))
        print("AUDIT_SUMMARY "+json.dumps({"pages":len(results),"min_similarity":min(r["similarity"] for r in results),"all_exact":all(r["exact_match"] for r in results)}))
if __name__=="__main__":main()
