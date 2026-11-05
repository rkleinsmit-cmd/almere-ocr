#!/usr/bin/env python3
"""Bounded GitHub OCR queue worker. No PDF or recognized text enters GitHub logs."""
import csv
import hashlib
import io
import json
import os
import statistics
import subprocess
import tempfile
import urllib.error
import urllib.request
from pathlib import Path

URL="https://yfnxuhuxdagomklpgswh.supabase.co/functions/v1/ocr-github-queue-worker-v1"
AUDIENCE="almere-ocr-worker-v1"

def post(token, payload, pdf=False):
    request=urllib.request.Request(URL,data=json.dumps(payload,ensure_ascii=False).encode("utf-8"),
       headers={"Authorization":"Bearer "+token,"Content-Type":"application/json"},method="POST")
    try:
        with urllib.request.urlopen(request,timeout=120) as response:
            return response.read(35000001 if pdf else 150000)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"Worker API HTTP {exc.code}: {exc.read(300).decode('utf-8',errors='replace')}") from None

def oidc_token():
    request_url=os.environ["ACTIONS_ID_TOKEN_REQUEST_URL"]
    separator="&" if "?" in request_url else "?"
    request=urllib.request.Request(request_url+separator+"audience="+AUDIENCE,
       headers={"Authorization":"Bearer "+os.environ["ACTIONS_ID_TOKEN_REQUEST_TOKEN"]})
    with urllib.request.urlopen(request,timeout=20) as response:
        return json.load(response)["value"]

def execute(*args,timeout=600):
    return subprocess.run(args,capture_output=True,text=True,check=True,timeout=timeout).stdout

def main():
    token=oidc_token()
    worker="github-"+os.environ["GITHUB_RUN_ID"]
    claim=json.loads(post(token,{"action":"claim","worker":worker}))
    job=claim.get("job")
    if not job:
        print("No job available; worker is disabled, capped, or queue is empty.")
        return
    document_id,page,lease=job["document_id"],job["page"],job["lease_token"]
    try:
        with tempfile.TemporaryDirectory(prefix="ocr_queue_") as folder:
            folder=Path(folder)
            pdf=folder/"source.pdf"
            raw=post(token,{"action":"source","document_id":document_id,"page":page,"lease_token":lease},pdf=True)
            if len(raw)>35000000 or not raw.startswith(b"%PDF-"):
                raise ValueError("Invalid or oversized PDF")
            pdf.write_bytes(raw)
            page_count=int(next(line.split(":",1)[1].strip() for line in execute("pdfinfo",str(pdf)).splitlines() if line.startswith("Pages:")))
            if page>page_count:raise ValueError("Page exceeds PDF page count")
            prefix=folder/"page"
            execute("pdftoppm","-f",str(page),"-l",str(page),"-r","300","-singlefile","-gray","-png",str(pdf),str(prefix))
            tsv=execute("tesseract",str(folder/"page.png"),"stdout","-l","nld+eng","--psm","3","tsv")
            words=[r for r in csv.DictReader(io.StringIO(tsv),delimiter="\t") if r["level"]=="5" and r["text"].strip()]
            lines={}
            for w in words:
                key=(w["block_num"],w["par_num"],w["line_num"])
                lines.setdefault(key,[]).append(w["text"])
            text="\n".join(" ".join(line) for line in lines.values())
            if len(text)<100:raise ValueError("ocr_text_too_short: needs manual review")
            conf=[float(w["conf"]) for w in words if float(w["conf"])>=0]
            payload={"action":"result","document_id":document_id,"page":page,"lease_token":lease,
                "engine":"tesseract-nld-eng","dpi":300,"text":text,
                "statistics":{"recognized_words":len(words),"recognized_characters":len(text),
                  "mean_word_confidence":round(statistics.mean(conf),1) if conf else None,
                  "source_sha256":hashlib.sha256(raw).hexdigest()}}
            result=json.loads(post(token,payload))
            if not result.get("ok"):raise RuntimeError("Completion not acknowledged")
            print(json.dumps({"status":"completed","document_id":document_id,"page":page,
              "extractie_id":result.get("extractie_id"),"recognized_words":len(words)}))
    except Exception as exc:
        try:
            post(token,{"action":"fail","document_id":document_id,"page":page,"lease_token":lease,
               "error":str(exc)[:300]})
        except Exception:
            print("Unable to release lease; lease expiry will recover it.")
        raise

if __name__=="__main__":
    main()
