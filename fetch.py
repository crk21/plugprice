#!/usr/bin/env python3
"""Pull AFDC public DC fast stations, save dated snapshot, diff vs previous snapshot."""
import json, os, sys, datetime, urllib.request, glob
ROOT = os.path.dirname(os.path.abspath(__file__))
SNAP = os.path.join(ROOT, "data/snapshots"); HIST = os.path.join(ROOT, "data/history")
KEY = os.environ.get("AFDC_API_KEY", "DEMO_KEY")
URL = ("https://developer.nlr.gov/api/alt-fuel-stations/v1.json?fuel_type=ELEC"
       "&ev_charging_level=dc_fast&status=all&access=public&limit=all&api_key=" + KEY)
KEEP = ["id","station_name","street_address","city","state","zip","latitude","longitude","status_code",
        "date_last_confirmed","updated_at","open_date","expected_date","ev_network","ev_network_web",
        "ev_dc_fast_num","ev_level2_evse_num","ev_connector_types","ev_pricing","access_days_time","facility_type"]

def slim(s): return {k: s.get(k) for k in KEEP}

def main():
    os.makedirs(SNAP, exist_ok=True); os.makedirs(HIST, exist_ok=True)
    today = datetime.date.today().isoformat()
    if len(sys.argv) > 1 and sys.argv[1] == "--from-raw":   # bootstrap from an existing raw dump
        raw = json.load(open(sys.argv[2]))
    else:
        req = urllib.request.Request(URL, headers={"User-Agent": "PlugPrice/0.1"})
        raw = json.load(urllib.request.urlopen(req, timeout=300))
    st = raw["fuel_stations"]
    if len(st) < 5000: sys.exit(f"Suspiciously few stations ({len(st)}); not saving.")
    snap = {"fetched": today, "source": URL.replace(KEY, "KEY"), "stations": [slim(s) for s in st]}
    latest = os.path.join(SNAP, "latest.json")
    prev = json.load(open(latest)) if os.path.exists(latest) else None
    if prev and prev.get("fetched") == today and os.path.exists(os.path.join(HIST, today + ".json")):
        prev = None  # re-run same day: keep existing diff
    # one station per line -> small git deltas day to day
    with open(latest, "w") as fh:
        fh.write('{"fetched":%s,"source":%s,"stations":[\n' % (json.dumps(today), json.dumps(snap["source"])))
        fh.write(",\n".join(json.dumps(s, separators=(",", ":"), sort_keys=True) for s in snap["stations"]))
        fh.write("\n]}\n")
    print(f"saved {len(st)} stations -> snapshots/latest.json")
    if not prev or prev.get("fetched") == today: print("no previous snapshot; no diff"); return
    old = {s["id"]: s for s in prev["stations"]}
    new = {s["id"]: s for s in snap["stations"]}
    ev = []
    for i, s in new.items():
        o = old.get(i)
        if o is None: ev.append({"id": i, "type": "added", "status": s["status_code"]}); continue
        a, b = o["status_code"], s["status_code"]
        if a != b:
            t = "went_down" if b == "T" else ("came_back" if a == "T" and b == "E" else "status_change")
            ev.append({"id": i, "type": t, "from": a, "to": b})
    ev += [{"id": i, "type": "removed", "from": o["status_code"]} for i, o in old.items() if i not in new]
    out = {"date": today, "previous": prev["fetched"], "events": ev}
    json.dump(out, open(os.path.join(HIST, today + ".json"), "w"), indent=0)
    from collections import Counter
    print("diff vs", out["previous"], dict(Counter(e["type"] for e in ev)))

if __name__ == "__main__": main()
