"""Download every archived version of the Consumer Council pump-price CSV from data.gov.hk."""
import json, pathlib, time, urllib.parse, urllib.request

SRC = "https://www.consumer.org.hk/pricewatch/oilwatch/opendata/oilprice_en.csv"
API = "https://api.data.gov.hk/v1/historical-archive"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data/raw/hk_archive"


def get(url):
    with urllib.request.urlopen(url, timeout=60) as r:
        return r.read()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    q = urllib.parse.urlencode({"url": SRC, "start": "20100101", "end": time.strftime("%Y%m%d")})
    stamps = json.loads(get(f"{API}/list-file-versions?{q}"))["timestamps"]
    new = 0
    for ts in stamps:
        f = OUT / f"{ts}.csv"
        if f.exists():
            continue
        q = urllib.parse.urlencode({"url": SRC, "time": ts})
        f.write_bytes(get(f"{API}/get-file?{q}"))
        new += 1
        time.sleep(0.2)
    print(f"{len(stamps)} versions listed, {new} downloaded")


if __name__ == "__main__":
    main()
