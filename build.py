#!/usr/bin/env python3
"""Generate the PlugPrice static site from the latest AFDC snapshot into ./site"""
import json, os, re, glob, shutil, html
from collections import Counter, defaultdict
ROOT = os.path.dirname(os.path.abspath(__file__)); OUT = os.path.join(ROOT, "site")
BASE_URL = os.environ.get("BASE_URL", "https://crk21.github.io/plugprice").rstrip("/")
REPORT_EMAIL = "chetan+prices@mail.grokbot.com"
STATES = {"AL":"Alabama","AK":"Alaska","AZ":"Arizona","AR":"Arkansas","CA":"California","CO":"Colorado","CT":"Connecticut","DE":"Delaware","DC":"District of Columbia","FL":"Florida","GA":"Georgia","HI":"Hawaii","ID":"Idaho","IL":"Illinois","IN":"Indiana","IA":"Iowa","KS":"Kansas","KY":"Kentucky","LA":"Louisiana","ME":"Maine","MD":"Maryland","MA":"Massachusetts","MI":"Michigan","MN":"Minnesota","MS":"Mississippi","MO":"Missouri","MT":"Montana","NE":"Nebraska","NV":"Nevada","NH":"New Hampshire","NJ":"New Jersey","NM":"New Mexico","NY":"New York","NC":"North Carolina","ND":"North Dakota","OH":"Ohio","OK":"Oklahoma","OR":"Oregon","PA":"Pennsylvania","PR":"Puerto Rico","RI":"Rhode Island","SC":"South Carolina","SD":"South Dakota","TN":"Tennessee","TX":"Texas","UT":"Utah","VT":"Vermont","VA":"Virginia","WA":"Washington","WV":"West Virginia","WI":"Wisconsin","WY":"Wyoming"}
STATUS = {"E":"Available","T":"Temporarily unavailable","P":"Planned"}
e = lambda x: html.escape(str(x if x is not None else ""))

def price_per_kwh(s):
    """Conservative: exactly one $ / ¢ amount in the string, tied to kWh, no time-of-use/peak, plausible range."""
    if not s: return None
    t = s.lower()
    if any(w in t for w in ("peak","pm","am ","member","level 2","l2","tier","up to","from","-$","range")): return None
    if len(re.findall(r"\$|¢|cents?", t)) != 1: return None
    m = re.search(r"\$\s?(\d*\.\d+|\d+)\s*(?:/|per|a)\s*kwh", t) or re.search(r"(\d+(?:\.\d+)?)\s*(?:¢|cents?)\s*(?:/|per|a)\s*kwh", t)
    if not m: return None
    v = float(m.group(1)); v = v/100 if "$" not in m.group(0) else v
    return round(v, 2) if 0.05 <= v <= 1.5 else None

BH_FORM = '<script async src="https://subscribe-forms.beehiiv.com/v3/loader.js" data-beehiiv-form="49ea30b7-47c6-4b01-9519-bd2b286493ce"></script>'
BH_ATTR = '<script type="text/javascript" async src="https://subscribe-forms.beehiiv.com/attribution.js"></script>'
PITCH = "Weekly: cheapest fast charging + which networks are broken. Free."
SUB_URL = "https://plugprice.beehiiv.com/subscribe"
def disc_note(pre=""): return f'<p class="note disc"><small>PlugPrice may earn a commission from some links on this page, at no extra cost to you. Data and rankings are never paid for. <a href="{pre}disclosure/index.html">Disclosure</a>.</small></p>'
def news(compact=False):
    if compact: return f'<aside class="news compact"><p><b>{PITCH}</b> <a href="{SUB_URL}">Subscribe</a></p>{BH_FORM}</aside>'
    return f'<section class="news"><h2>Get the weekly PlugPrice email</h2><p>{PITCH}</p>{BH_FORM}<p><small>Form not loading? <a href="{SUB_URL}">Subscribe here</a>.</small></p></section>'

def page(path, title, body, desc="", depth=None):
    if path == "index.html" or path.startswith(("leaderboard/", "prices/", "state/")): body += news()
    elif path.startswith("station/"): body += news(True)
    attr = BH_ATTR if "beehiiv" in body else ""
    d = path.count("/"); pre = "../" * d
    nav = f'<nav><a class="logo" href="{pre}index.html">⚡ PlugPrice</a><a href="{pre}leaderboard/index.html">Reliability</a><a href="{pre}prices/index.html">Prices</a><a href="{pre}about/index.html">About</a></nav>'
    doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{e(title)}</title><meta name="description" content="{e(desc or title)}"><link rel="canonical" href="{BASE_URL}/{path[:-10] if path.endswith('index.html') else path}"><link rel="stylesheet" href="{pre}style.css"></head>
<body><header>{nav}</header><main>{body}</main><footer>Data: <a href="https://afdc.energy.gov/stations">U.S. DOE Alternative Fuels Data Center</a>, snapshot {SNAPDATE}. PlugPrice is independent and not affiliated with DOE or any network. <a href="{pre}about/index.html">Caveats</a> · <a href="{pre}privacy/index.html">Privacy</a> · <a href="{pre}disclosure/index.html">Affiliate disclosure</a></footer>
<script>window.ROOT="{pre}"</script>{'<script src="'+pre+'app.js"></script>' if 'data-app' in body else ''}{attr}</body></html>"""
    f = os.path.join(OUT, path); os.makedirs(os.path.dirname(f), exist_ok=True)
    open(f, "w").write(doc); PAGES.append(path)

PAGES = []
def pct(a, b): return f"{100*a/b:.1f}%" if b else "–"

def table(rows, depth):
    pre = "../" * depth
    r = "".join(f'<tr class="s{s["status_code"]}"><td><a href="{pre}station/{s["id"]}/index.html">{e(s["station_name"])}</a><br><small>{e(s["street_address"])}, {e(s["city"])}</small></td><td>{e(s["ev_network"])}</td><td>{s["ev_dc_fast_num"] or 0}</td><td><span class="b{s["status_code"]}">{STATUS.get(s["status_code"],s["status_code"])}</span></td><td>{("$%.2f/kWh" % s["_p"]) if s["_p"] else "—"}</td></tr>' for s in rows)
    return f'<div class="tw"><table><thead><tr><th>Station</th><th>Network</th><th>DC ports</th><th>Status</th><th>Price</th></tr></thead><tbody>{r}</tbody></table></div>'

def main():
    global SNAPDATE
    snap = json.load(open(os.path.join(ROOT, "data/snapshots/latest.json")))
    SNAPDATE = snap["fetched"]; S = snap["stations"]
    for s in S: s["_p"] = price_per_kwh(s.get("ev_pricing")); s["ev_network"] = s["ev_network"] or "Unknown"
    if os.path.exists(OUT): shutil.rmtree(OUT)
    os.makedirs(OUT); shutil.copy(os.path.join(ROOT, "static/style.css"), OUT); shutil.copy(os.path.join(ROOT, "static/app.js"), OUT)
    live = [s for s in S if s["status_code"] in "ET"]
    nT = sum(s["status_code"] == "T" for s in S); ports = sum(s["ev_dc_fast_num"] or 0 for s in S)
    # history events
    hist = []
    for h in sorted(glob.glob(os.path.join(ROOT, "data/history/*.json")))[-14:]:
        hd = json.load(open(h)); hist += [(hd["date"], ev) for ev in hd["events"]]
    byid = {s["id"]: s for s in S}
    # leaderboards (denominator = E+T stations; planned excluded)
    def board(key, minn):
        g = defaultdict(lambda: [0, 0, 0])
        for s in live:
            x = g[s[key]]; x[0] += 1; x[1] += s["status_code"] == "T"; x[2] += s["ev_dc_fast_num"] or 0
        return sorted(((k, *v) for k, v in g.items() if v[0] >= minn), key=lambda r: (-r[2]/r[1], -r[1]))
    nets = board("ev_network", 50); sts = board("state", 1)
    json.dump({"date": SNAPDATE, "networks": [[k, n, t, round(100*t/n, 2)] for k, n, t, _ in nets]}, open(os.path.join(ROOT, "data/leaderboard_latest.json"), "w"), indent=1)
    def lbt(rows, kind):
        r = ""
        for i, (k, n, t, p) in enumerate(rows, 1):
            name = f'<a href="../state/{k.lower()}/index.html">{e(STATES.get(k, k))}</a>' if kind == "s" else e(k)
            r += f'<tr><td>{i}</td><td>{name}</td><td>{n:,}</td><td>{t:,}</td><td><div class="bar"><i style="width:{min(100, 100*t/n*5):.0f}%"></i></div>{pct(t, n)}</td></tr>'
        return f'<div class="tw"><table><thead><tr><th>#</th><th>{"Network" if kind=="n" else "State"}</th><th>Stations</th><th>Temp. unavailable</th><th>% down</th></tr></thead><tbody>{r}</tbody></table></div>'
    page("leaderboard/index.html", "EV fast charging network reliability leaderboard – PlugPrice", f"""
<h1>Which fast-charging networks are down the most?</h1>
<p class="note">Share of public DC fast stations each network has flagged <b>temporarily unavailable</b> (AFDC status “T”) on {SNAPDATE}. Denominator = open + temporarily unavailable stations (planned excluded). Networks with ≥50 stations only. This is a single-day, station-level flag reported by networks/DOE — not a measured per-port uptime. Daily history accrues from here on.</p>
<h2>By network</h2>{lbt(nets, "n")}<h2>By state</h2>{lbt(sts, "s")}""", "Percent of DC fast charging stations temporarily unavailable, by network and state.")
    # prices
    pr = [s for s in S if s["_p"] and s["status_code"] != "P"]
    bys = defaultdict(list)
    for s in pr: bys[s["state"]].append(s)
    body = f'<h1>Known DC fast charging prices ($/kWh)</h1><p class="note">{len(pr):,} of {len(S):,} stations ({pct(len(pr), len(S))}) list a single unambiguous $/kWh price in AFDC. We skip time-of-use, tiered, per-minute, “free” and anything ambiguous. Prices may be stale and may exclude session/idle fees — check the app before you plug in. <a href="mailto:{REPORT_EMAIL}?subject=Price%20report">Report a price</a>.</p><p>Jump to: ' + " ".join(f'<a href="#{k}">{k}</a>' for k in sorted(bys)) + "</p>"
    for k in sorted(bys):
        body += f'<h2 id="{k}">{e(STATES.get(k, k))} <small>({len(bys[k])})</small></h2>' + table(sorted(bys[k], key=lambda s: s["_p"]), 1)
    page("prices/index.html", "Cheapest EV fast charging prices by state ($/kWh) – PlugPrice", body)
    # state pages
    stc = defaultdict(list)
    for s in S: stc[s["state"]].append(s)
    statelinks = []
    for k, L in sorted(stc.items()):
        nm = STATES.get(k, k); t = sum(s["status_code"] == "T" for s in L); lv = sum(s["status_code"] in "ET" for s in L)
        cities = Counter(s["city"] for s in L).most_common(15)
        nw = Counter(s["ev_network"] for s in L).most_common(8)
        L = sorted(L, key=lambda s: ({"T": 0, "E": 1, "P": 2}.get(s["status_code"], 3), s["city"] or "", s["station_name"]))
        body = f"""<h1>EV fast chargers in {e(nm)}</h1>
<div class="stats"><div><b>{len(L):,}</b>stations</div><div><b>{sum(s['ev_dc_fast_num'] or 0 for s in L):,}</b>DC fast ports</div><div><b>{t}</b>temporarily unavailable ({pct(t, lv)})</div><div><b>{sum(1 for s in L if s['_p'])}</b>with known price</div></div>
<h2>Top cities</h2><p class="chips">{"".join(f'<span>{e(c)} <b>{n}</b></span>' for c, n in cities)}</p>
<h2>Top networks</h2><p class="chips">{"".join(f'<span>{e(c)} <b>{n}</b></span>' for c, n in nw)}</p>
<h2>All stations <small>(unavailable first)</small></h2><input id="tf" placeholder="Filter by city, name or network…" data-app>{table(L, 2)}"""
        page(f"state/{k.lower()}/index.html", f"EV fast chargers in {nm}: prices & which are down – PlugPrice", body, f"{len(L)} DC fast charging stations in {nm}; {t} temporarily unavailable as of {SNAPDATE}.")
        statelinks.append((k, nm, len(L)))
    # station pages
    evs = defaultdict(list)
    for d, ev in hist: evs[ev["id"]].append((d, ev["type"]))
    for s in S:
        pre = "../../"
        price = f'<b>${s["_p"]:.2f}/kWh</b> <small>(as listed: “{e(s["ev_pricing"])}”)</small>' if s["_p"] else (f'Price not listed yet{" (listed as: “"+e(s["ev_pricing"])+"”)" if s["ev_pricing"] else ""} · <a href="mailto:{REPORT_EMAIL}?subject=Price%20for%20station%20{s["id"]}">Report a price</a>')
        h = "".join(f"<li>{d}: {t.replace('_', ' ')}</li>" for d, t in evs.get(s["id"], [])) or "<li>No status changes recorded yet (tracking started " + SNAPDATE + ").</li>"
        rows = [("Network", e(s["ev_network"]) + (f' · <a href="{e(s["ev_network_web"])}" rel="nofollow">site</a>' if s["ev_network_web"] else "")),
                ("Status", f'<span class="b{s["status_code"]}">{STATUS.get(s["status_code"], s["status_code"])}</span>' + (f' (expected {e(s["expected_date"])})' if s["expected_date"] else "")),
                ("Last confirmed", e(s["date_last_confirmed"] or "unknown")), ("DC fast ports", s["ev_dc_fast_num"] or 0),
                ("Level 2 ports", s["ev_level2_evse_num"] or 0), ("Connectors", e(", ".join(s["ev_connector_types"] or []))),
                ("Price", price), ("Hours", e(s["access_days_time"] or "–")),
                ("Address", f'{e(s["street_address"])}, {e(s["city"])}, {e(s["state"])} {e(s["zip"])} · <a href="https://www.google.com/maps/search/?api=1&query={s["latitude"]},{s["longitude"]}">Map</a>')]
        body = f'<p><a href="{pre}state/{(s["state"] or "").lower()}/index.html">← {e(STATES.get(s["state"], s["state"]))}</a></p><h1>{e(s["station_name"])}</h1><dl class="kv">' + "".join(f"<dt>{a}</dt><dd>{b}</dd>" for a, b in rows) + f'</dl><h2>Status history</h2><ul>{h}</ul><p class="note">AFDC station ID {s["id"]}. Status is reported by the network/DOE; it can lag reality.</p>'
        page(f"station/{s['id']}/index.html", f"{s['station_name']} – {s['city']}, {s['state']} EV fast charger – PlugPrice", body)
    # home search index (compact)
    idx = [[s["id"], s["station_name"], s["city"], s["state"], s["ev_network"], s["ev_dc_fast_num"] or 0, s["status_code"], s["_p"]] for s in S]
    os.makedirs(os.path.join(OUT, "data")); json.dump(idx, open(os.path.join(OUT, "data/stations.json"), "w"), separators=(",", ":"))
    down = [(d, ev) for d, ev in hist if ev["type"] in ("went_down", "came_back") and ev["id"] in byid][-20:]
    recent = "".join(f'<li>{d}: <a href="station/{ev["id"]}/index.html">{e(byid[ev["id"]]["station_name"])}</a> ({e(byid[ev["id"]]["city"])}, {byid[ev["id"]]["state"]}) {ev["type"].replace("_", " ")}</li>' for d, ev in reversed(down)) or "<li>No day-over-day changes yet — tracking started " + SNAPDATE + ".</li>"
    top = "".join(f"<li>{e(k)}: <b>{pct(t, n)}</b> of {n:,} stations down</li>" for k, n, t, _ in nets[:5])
    page("index.html", "PlugPrice – US EV fast chargers: which are down, and what they cost", f"""
<section class="hero"><h1>Find a fast charger that actually works.</h1><p>Every public DC fast charging station in the US, with today's reported status and prices where known.</p></section>
<div class="stats"><div><b>{len(S):,}</b>stations</div><div><b>{ports:,}</b>DC fast ports</div><div><b>{pct(nT, len(live))}</b>temporarily unavailable ({nT:,})</div><div><b>{len(pr):,}</b>with known $/kWh</div></div>
<h2>Search</h2><div class="filters" data-app><select id="fs"><option value="">All states</option>{"".join(f'<option value="{k}">{e(n)}</option>' for k, n, _ in statelinks)}</select><input id="fc" placeholder="City"><select id="fn"><option value="">All networks</option>{"".join(f'<option>{e(k)}</option>' for k, c in Counter(s["ev_network"] for s in S).most_common())}</select><label><input type="checkbox" id="fd"> Only down</label></div><div id="res"></div>
<h2>Least reliable networks today</h2><ol>{top}</ol><p><a href="leaderboard/index.html">Full reliability leaderboard →</a></p>
<h2>Recent status changes</h2><ul>{recent}</ul>
<h2>Browse by state</h2><p class="chips">{"".join(f'<a href="state/{k.lower()}/index.html">{e(n)} <b>{c}</b></a>' for k, n, c in statelinks)}</p>
<!-- home charger affiliate links go here -->{disc_note()}
""")
    page("about/index.html", "About PlugPrice & data caveats", f"""<h1>About PlugPrice</h1>
<p>PlugPrice tracks every public DC fast charging station in the US to show which ones are reported down and what they cost.</p>
<h2>Data source</h2><p>Station data comes from the <a href="https://afdc.energy.gov/stations">U.S. Department of Energy Alternative Fuels Data Center (AFDC)</a> Station Locator API (developer.nlr.gov, alt-fuel-stations v1), refreshed daily. Current snapshot: {SNAPDATE}. AFDC data is public; PlugPrice is not affiliated with or endorsed by DOE, NREL/NLR, or any charging network.</p>
<h2>Honest caveats</h2><ul>
<li><b>Status is station-level and self-reported.</b> “Temporarily unavailable” (AFDC code T) is set by networks/DOE. A station marked available may still have broken ports; we have no per-port uptime.</li>
<li><b>Reliability history starts {SNAPDATE}.</b> We compare daily snapshots to record when stations go down or come back. Trends need weeks of data.</li>
<li><b>Prices are sparse.</b> Only {pct(len(pr), len(S))} of stations list a single clear $/kWh price. Big networks (ChargePoint, EVgo, Electrify America…) publish none in AFDC. We skip time-of-use, tiered, per-minute and vague entries rather than guess. Listed prices may be outdated and may exclude session or idle fees.</li>
<li>Reliability leaderboard only ranks networks with at least 50 stations.</li></ul>
<h2>Contact</h2><p>Spot a wrong price or status? <a href="mailto:{REPORT_EMAIL}">Email us</a>.</p>""")
    page("privacy/index.html", "Privacy – PlugPrice", f"""<h1>Privacy</h1>
<p>Short version: PlugPrice collects as little as possible.</p>
<ul><li><b>No accounts.</b> There are no logins or user profiles here.</li>
<li><b>Newsletter.</b> If you sign up for the weekly email, your email address is collected and stored by <a href="https://plugprice.beehiiv.com">beehiiv</a>, which sends the newsletter. Its privacy policy applies, and you can unsubscribe from any email.</li>
<li><b>Hosting.</b> The site is hosted on GitHub Pages. GitHub may log technical data such as IP addresses for security and operations; see GitHub's privacy statement.</li>
<li><b>No ad trackers.</b> We currently run no ads, ad trackers, or third-party analytics. If that changes, this page will be updated first.</li></ul>
<h2>Contact</h2><p>Questions or requests: <a href="mailto:{REPORT_EMAIL}">{REPORT_EMAIL}</a></p>""")
    page("disclosure/index.html", "Affiliate disclosure – PlugPrice", f"""<h1>Affiliate disclosure</h1>
<p>PlugPrice may earn a commission when you buy through some links, such as links to home EV chargers. This costs you nothing extra.</p>
<p>Station data, prices, and reliability rankings are never paid for. No network or seller can buy a better position.</p>
<p>Questions: <a href="mailto:{REPORT_EMAIL}">{REPORT_EMAIL}</a></p>""")
    # sitemap(s) + robots
    urls = [BASE_URL + "/" + (p[:-10] if p.endswith("index.html") else p) for p in PAGES]
    chunks = [urls[i:i+45000] for i in range(0, len(urls), 45000)]
    def sm(u): return '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<url><loc>{html.escape(x)}</loc><lastmod>{SNAPDATE}</lastmod></url>\n" for x in u) + "</urlset>\n"
    if len(chunks) == 1: open(os.path.join(OUT, "sitemap.xml"), "w").write(sm(urls)); maps = ["sitemap.xml"]
    else:
        maps = []
        for i, c in enumerate(chunks, 1): open(os.path.join(OUT, f"sitemap-{i}.xml"), "w").write(sm(c)); maps.append(f"sitemap-{i}.xml")
        open(os.path.join(OUT, "sitemap.xml"), "w").write('<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n' + "".join(f"<sitemap><loc>{BASE_URL}/{m}</loc></sitemap>\n" for m in maps) + "</sitemapindex>\n")
    open(os.path.join(OUT, "robots.txt"), "w").write(f"User-agent: *\nAllow: /\nSitemap: {BASE_URL}/sitemap.xml\n")
    open(os.path.join(OUT, ".nojekyll"), "w").write("")
    n = sum(len(f) for _, _, f in os.walk(OUT)); print(f"built {n} files from snapshot {SNAPDATE}")

if __name__ == "__main__": main()
