"""Veilige verbindingsproef. Geen AI API, geen dossierclaim of mutatie."""
import os
import psycopg

def main():
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("ALMERE_DATABASE_URL ontbreekt; geen databasehandeling uitgevoerd")
    with psycopg.connect(url, connect_timeout=15, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT factcheck_runner_api.health()")
            status = cur.fetchone()[0]
            if isinstance(status, str):
                import json
                status = json.loads(status)
            safety = status.get("safety") or {}
            if (status.get("permit") != "ok"
                or safety.get("automatic_heavy_work_enabled") is not True
                or safety.get("paused_at") is not None
                or safety.get("pause_reason") is not None):
                raise RuntimeError("Opslagbeveiliging blokkeert verwerking")
            cur.execute("SELECT has_function_privilege(current_user, 'factcheck_runner_api.claim_one()', 'EXECUTE')")
            if cur.fetchone()[0] is not True:
                raise RuntimeError("Runner mist functieprivileges")
            print("Verbinding en veiligheidscontrole geslaagd; geen dossier geclaimd.")
            print("Volledige broncontrole en definitieve opslag nog niet geïmplementeerd.")

if __name__ == "__main__":
    main()
