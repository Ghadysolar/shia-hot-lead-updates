#!/usr/bin/env python3
"""
Daily pull of Shia's GoHighLevel "Espanol" pipeline hot-lead activity.

NOTE: by explicit choice of the repo owner, this writes full lead detail
(name, phone, email) to the public data files. This repo is PUBLIC, so
that data is visible to anyone with the link, indexed by search engines,
with no login. If that's ever not wanted anymore, strip the "contact"
block below and only keep the aggregate counts.
"""
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

API_KEY = os.environ.get("GHL_API_KEY")
if not API_KEY:
    print("GHL_API_KEY env var is not set", file=sys.stderr)
    sys.exit(1)

LOCATION_ID = "uZRaRw67eC05ttWdkWlC"
PIPELINE_ID = "OHFNPBSj2nLHCVRXI6At"  # "Espanol" pipeline
TZ_OFFSET_HOURS = 3  # Asia/Damascus, matches how "today" is defined elsewhere

HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Version": "2021-07-28",
    "Accept": "application/json",
}

STAGE_MAP = {
    "908fc045-b059-451e-9f26-efaa66c76e16": ("Hot Lead In", "hot"),
    "39f168b6-5645-4ead-842e-a830c723693b": ("Warm Lead", "hot"),
    "50d1cdb7-cd0a-4cde-a8a0-0d3f71759d57": ("Sin Respuesta (Seguimiento)", "contacted"),
    "2b9077dc-f81a-4326-9694-2c121097d428": ("Contactado", "contacted"),
    "8c1692d5-9baf-4ec5-91c6-c28231b22cfd": ("CALL LATER", "contacted"),
    "c485505b-3b6d-4b11-b079-c0923ab5a52b": ("Sin respuesta y contactado Karina", "contacted"),
    "083ff088-a07a-4dc7-9e42-ecc63f0b1160": ("Sin respuests y contactado Daglys", "contacted"),
    "6f68caac-2201-41ca-a654-905e4343e6b3": ("Cita Agendada", "booked"),
    "f04f2b59-8931-4954-a960-3193723eb91c": ("No se presento", "booked"),
    "10c81304-c720-4b31-8d75-9c34121206b5": ("No se presento y sentado Karina", "booked"),
    "c739f344-eac5-4c04-86be-f25f60af1cab": ("No se presento y sentado Daglys", "booked"),
    "54ff27ba-d93a-4064-83fe-cd64c746c66a": ("Sentado", "booked"),
    "c837d2eb-4c56-47d3-96c9-f79716acd374": ("Credito Fallido", "booked"),
    "5876b3aa-b7ac-4825-b0d0-04746c69f810": ("Cerrado", "booked"),
    "8e20d4f2-b540-4d08-937c-e6f36c61542a": ("Referido", "booked"),
    "ba93d8fc-acdf-450c-a624-e47a32e1215d": ("Descalificado", "booked"),
    "32de379e-eae0-4613-b1fa-a70c3e5012cf": ("Leads extranos y Fuera de zona", "booked"),
    "1d743108-1f58-4079-bcf2-c59f432daaa0": ("Instalados Shia", "booked"),
    "9c158f5d-e8e1-41b3-9564-851f240cb4a3": ("cancelados nuevos", "booked"),
    "b725c9c1-5656-4f13-8552-8b1b0071bb82": ("Cancelados y abandonados", "booked"),
    "f300792a-f145-4e26-89b2-ae72b06a5f62": ("Mobile Home", "booked"),
    "2f012c57-d1f1-4019-81f3-c8f3ba95e026": ("DQ por credito", "booked"),
    "7e2a4684-1e91-4cbb-93e0-eca49d1092cf": ("Permisos aprobados", "booked"),
    "6879669b-3289-4deb-8178-4f7c34861b9a": ("Dealmachine", "booked"),
    "73365ce6-7046-4a7a-b831-b32aee791af9": ("Proyectos Activos", "booked"),
    "3573c77d-a538-44cb-866e-82a36e8cd36b": ("PROX MES", "booked"),
}


def fetch_json(url: str) -> dict:
    req = Request(url, headers=HEADERS)
    try:
        with urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except HTTPError as e:
        print(f"GHL API error {e.code} for {url}: {e.read()[:500]}", file=sys.stderr)
        raise


def damascus_midnight_utc(now: datetime) -> datetime:
    local = now + timedelta(hours=TZ_OFFSET_HOURS)
    local_midnight = local.replace(hour=0, minute=0, second=0, microsecond=0)
    return local_midnight - timedelta(hours=TZ_OFFSET_HOURS)


def main():
    now = datetime.now(timezone.utc)
    cutoff = damascus_midnight_utc(now)
    date_label = (cutoff + timedelta(hours=TZ_OFFSET_HOURS)).strftime("%Y-%m-%d")

    users_data = fetch_json(f"https://services.leadconnectorhq.com/users/?locationId={LOCATION_ID}")
    user_map = {u["id"]: (u.get("name") or "").strip() for u in users_data.get("users", [])}

    base = "https://services.leadconnectorhq.com/opportunities/search"
    start_after = None
    start_after_id = None
    page = 0
    leads = []
    stop = False

    while not stop and page < 40:
        url = f"{base}?location_id={LOCATION_ID}&pipeline_id={PIPELINE_ID}&limit=100"
        if start_after:
            url += f"&startAfter={start_after}&startAfterId={start_after_id}"
        data = fetch_json(url)
        opportunities = data.get("opportunities") or []
        if not opportunities:
            break
        for o in opportunities:
            last_change = datetime.fromisoformat(o["lastStatusChangeAt"].replace("Z", "+00:00"))
            if last_change < cutoff:
                stop = True
                break
            created = datetime.fromisoformat(o["createdAt"].replace("Z", "+00:00"))
            if created >= cutoff:
                stage_id = o.get("pipelineStageId")
                name, bucket = STAGE_MAP.get(stage_id, ("Unknown stage", "other"))
                contact = o.get("contact") or {}
                leads.append({
                    "name": o.get("name"),
                    "stage": name,
                    "bucket": bucket,
                    "createdAt": o.get("createdAt"),
                    "rep": user_map.get(o.get("assignedTo")),
                    "email": contact.get("email"),
                    "phone": contact.get("phone"),
                })
        if stop:
            break
        meta = data.get("meta") or {}
        if not meta.get("startAfter") or len(opportunities) < 100:
            break
        start_after = meta["startAfter"]
        start_after_id = meta["startAfterId"]
        page += 1

    leads.sort(key=lambda l: l["createdAt"], reverse=True)

    totals = {"hot": 0, "contacted": 0, "booked": 0}
    stage_counts = {}
    for l in leads:
        totals[l["bucket"]] = totals.get(l["bucket"], 0) + 1
        stage_counts.setdefault(l["stage"], {"stage": l["stage"], "bucket": l["bucket"], "count": 0})
        stage_counts[l["stage"]]["count"] += 1
    breakdown = sorted(stage_counts.values(), key=lambda b: -b["count"])

    payload = {
        "date": date_label,
        "generatedAt": now.isoformat().replace("+00:00", "Z"),
        "totalHotLeads": len(leads),
        "totals": totals,
        "stageBreakdown": breakdown,
        "leads": leads,
    }

    repo_root = Path(__file__).resolve().parents[1]
    data_dir = repo_root / "data"
    days_dir = data_dir / "days"
    days_dir.mkdir(parents=True, exist_ok=True)

    (data_dir / "latest.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    (days_dir / f"{date_label}.json").write_text(json.dumps(payload, indent=2, ensure_ascii=False))

    manifest_path = data_dir / "manifest.json"
    dates = sorted({p.stem for p in days_dir.glob("*.json")}, reverse=True)
    manifest_path.write_text(json.dumps({"dates": dates}, indent=2))

    print(f"Wrote {date_label}: {payload['totals']} (total {len(leads)})")


if __name__ == "__main__":
    main()
