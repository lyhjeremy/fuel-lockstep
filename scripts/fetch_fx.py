"""HKD per USD and AUD per USD, daily, from FRED (no key) into data/fx.csv."""
import io, pathlib, urllib.request
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://fred.stlouisfed.org/graph/fredgraph.csv?id={}"


def main():
    frames = []
    for name, code in {"hkd_per_usd": "DEXHKUS", "usd_per_aud": "DEXUSAL"}.items():
        d = pd.read_csv(io.BytesIO(urllib.request.urlopen(URL.format(code), timeout=60).read()))
        d.columns = ["date", "value"]
        d["value"] = pd.to_numeric(d.value, errors="coerce")
        d["series"] = name
        frames.append(d.dropna())
    out = pd.concat(frames)
    out.to_csv(ROOT / "data/fx.csv", index=False)
    print(out.groupby("series").date.agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()
