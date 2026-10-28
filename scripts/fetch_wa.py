"""Download FuelWatch monthly retail files (Western Australia) and keep Perth metro ULP rows.

Raw monthly files are large, so they go to FUEL_CACHE (default data/raw/wa, gitignored).
The kept panel is written to data/wa_perth_ulp.csv.gz.
"""
import io, os, pathlib, time, urllib.request
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = pathlib.Path(os.environ.get("FUEL_CACHE", ROOT / "data/raw/wa"))
URL = "https://warsydprdstafuelwatch.blob.core.windows.net/historical-reports/FuelWatchRetail-{:02d}-{}.csv"
START, END = (2020, 1), (2026, 9)


def months():
    y, m = START
    while (y, m) <= END:
        yield y, m
        y, m = (y + 1, 1) if m == 12 else (y, m + 1)


def main():
    CACHE.mkdir(parents=True, exist_ok=True)
    keep = []
    for y, m in months():
        f = CACHE / f"{y}-{m:02d}.csv"
        if not f.exists():
            f.write_bytes(urllib.request.urlopen(URL.format(m, y), timeout=120).read())
            time.sleep(0.5)
        d = pd.read_csv(f, encoding="latin-1")
        d = d[(d.PRODUCT_DESCRIPTION == "ULP") & (d.REGION_DESCRIPTION == "Metro")]
        keep.append(d[["PUBLISH_DATE", "TRADING_NAME", "BRAND_DESCRIPTION", "PRODUCT_PRICE", "ADDRESS", "LOCATION", "POSTCODE"]])
    out = pd.concat(keep)
    out["PUBLISH_DATE"] = pd.to_datetime(out.PUBLISH_DATE, dayfirst=True)
    out.columns = ["date", "station", "brand", "price_cents_l", "address", "suburb", "postcode"]
    # A station is a site (name plus address); its brand can change over time, so brand stays on the price rows.
    sites = out[["station", "address", "suburb", "postcode"]].drop_duplicates(["station", "address"]).reset_index(drop=True)
    sites.insert(0, "station_id", sites.index + 1)
    out = out.merge(sites[["station_id", "station", "address"]], on=["station", "address"])
    sites.to_csv(ROOT / "data/wa_perth_stations.csv", index=False)
    out = out[["date", "station_id", "brand", "price_cents_l"]].sort_values(["date", "station_id"])
    out.to_csv(ROOT / "data/wa_perth_ulp.csv.gz", index=False)
    print(len(out), "rows,", out.station_id.nunique(), "stations,", out.date.min().date(), "to", out.date.max().date())


if __name__ == "__main__":
    main()
