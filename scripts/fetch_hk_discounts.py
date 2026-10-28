"""Walk-in discounts by brand from Internet Archive snapshots of the Consumer Council's Oil Price Watch page.

The live page shows, for each brand and grade, the pump price, the net price after the walk-in
discount, and the discount. The Council does not publish this table as a dataset, so the history
comes from Wayback Machine captures of the Chinese and English home pages (one per day at most).
Raw pages go to data/raw/wayback (gitignored); the parsed table goes to data/hk_walkin_discounts.csv.
"""
import html, json, pathlib, re, time, urllib.parse, urllib.request
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/wayback"
PAGES = ["oil-price.consumer.org.hk/tc/", "oil-price.consumer.org.hk/en/"]
BRANDS = {"中石化": "Sinopec", "中國石油": "PetroChina", "加德士": "Caltex", "埃索": "Esso", "蜆殼": "Shell",
          "Sinopec": "Sinopec", "PetroChina": "PetroChina", "Caltex": "Caltex", "Esso": "Esso", "Shell": "Shell"}
# Section headers that open each grade's comparison table, Chinese then English. The Chinese
# standard header is a suffix of the premium one, hence the lookbehind.
GRADES = [("standard", r"(?<!特級)無鉛汽油 零售牌價 折後價 門市折扣|Standard Petrol Pump Price Net Price after Walk-in Discount Walk-in Discount"),
          ("premium", r"特級無鉛汽油 零售牌價 折後價 門市折扣|Premium Petrol Pump Price Net Price after Walk-in Discount Walk-in Discount")]
ROW = re.compile(r"(中石化|中國石油|加德士|埃索|蜆殼|Sinopec|PetroChina|Caltex|Esso|Shell) \$([\d.]+) \$([\d.]+) \(-\$([\d.]+)\)")


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "fuel-lockstep research (github.com/lyhjeremy)"})
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=90) as r:
                return r.read()
        except Exception:
            time.sleep(5 * (attempt + 1))
    raise RuntimeError(url)


def snapshots():
    seen = {}
    for page in PAGES:
        q = urllib.parse.urlencode({"url": page, "output": "json", "fl": "timestamp", "filter": "statuscode:200", "collapse": "timestamp:8"})
        for (ts,) in json.loads(get(f"https://web.archive.org/cdx/search/cdx?{q}"))[1:]:
            seen.setdefault(ts[:8], (ts, page))
    return sorted(seen.values())


def parse(raw: bytes):
    t = raw.decode("utf-8", errors="ignore")
    t = re.sub(r"(?s)<(script|style).*?</\1>", "", t)
    s = re.sub(r"\s+", " ", html.unescape(re.sub(r"<[^>]+>", " ", t)))
    rows = []
    for grade, header in GRADES:
        m = list(re.finditer(header, s))
        if not m:
            continue
        block = s[m[-1].end(): m[-1].end() + 400]
        for b, pump, net, disc in ROW.findall(block)[:5]:
            rows.append((grade, BRANDS[b], float(pump), float(net), float(disc)))
    return rows


def main():
    RAW.mkdir(parents=True, exist_ok=True)
    out = []
    for ts, page in snapshots():
        f = RAW / f"{ts}.html"
        if not f.exists():
            f.write_bytes(get(f"https://web.archive.org/web/{ts}id_/https://{page}"))
            time.sleep(1.5)
        for row in parse(f.read_bytes()):
            out.append((pd.to_datetime(ts[:8]).date(), ts, *row))
    d = pd.DataFrame(out, columns=["date", "capture", "grade", "brand", "pump", "net", "walkin_discount"])
    d.to_csv(ROOT / "data/hk_walkin_discounts.csv", index=False)
    print(len(d), "rows,", d.date.nunique(), "days,", d.date.min(), "to", d.date.max())


if __name__ == "__main__":
    main()
