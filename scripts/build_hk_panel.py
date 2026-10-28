"""Turn the archived Consumer Council CSVs into a brand-by-day panel of posted prices.

Each archive file is a snapshot taken when the source file changed. The panel carries the
latest snapshot forward to every calendar day, so a price "change day" is the first day a
new price appears in a snapshot.
"""
import csv, io, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RAW = ROOT / "data/raw/hk_archive"

GRADE = {
    "unleaded gasoline (regular)": "standard",
    "standard petrol": "standard",
    "unleaded gasoline (premium)": "premium",
    "premium petrol": "premium",
    "super petrol": "premium",
    "diesel": "diesel",
    "ultra low sulphur diesel": "diesel",
}
BRAND = {"petrochina": "PetroChina", "sinopec": "Sinopec", "caltex": "Caltex", "esso": "Esso", "shell": "Shell"}


def read(f):
    text = f.read_text(encoding="utf-8-sig")
    rows = list(csv.reader(io.StringIO(text)))
    header, body = rows[0], rows[1:]
    out = []
    for r in body:
        if len(r) < 3 or not r[2].strip():
            continue
        out.append((GRADE.get(r[0].strip().lower(), r[0].strip()), BRAND.get(r[1].strip().lower(), r[1].strip()), float(r[2])))
    return header[2].replace("\n", " "), out


def main():
    snaps, labels = [], set()
    for f in sorted(RAW.glob("*.csv")):
        label, rows = read(f)
        labels.add(label)
        ts = pd.to_datetime(f.stem, format="%Y%m%d-%H%M")
        snaps += [(ts, g, b, p, label) for g, b, p in rows]
    s = pd.DataFrame(snaps, columns=["snapshot", "grade", "brand", "price", "label"])
    print("price column labels:", labels)
    print("grades:", s.grade.unique(), "brands:", s.brand.unique())
    s.to_csv(ROOT / "data/hk_snapshots.csv.gz", index=False)

    # Feed fault: on some snapshots one brand's premium price is reported equal to its own
    # standard price and reverts at the next snapshot. A brand can genuinely price both grades
    # the same for a while (PetroChina did in late 2020), so only a match that lasts a single
    # snapshot, with a premium surcharge on both sides of it, is dropped (docs/decisions.md, D3).
    w = s.pivot_table(index="snapshot", columns=["grade", "brand"], values="price")
    eq = (w["premium"] - w["standard"]).round(4) == 0
    isolated = eq & ~eq.shift(1, fill_value=False) & ~eq.shift(-1, fill_value=False) & eq.shift(1).notna() & eq.shift(-1).notna()
    isolated.iloc[[0, -1]] = False
    bad = isolated.stack().loc[lambda x: x].index
    drop = s.set_index(["snapshot", "brand"]).index.isin(bad) & (s.grade == "premium").values
    print("premium rows dropped as one-snapshot feed faults:", int(drop.sum()), "of", int(eq.sum().sum()), "premium = standard rows")
    s = s[~drop]

    s["date"] = s.snapshot.dt.normalize()
    last = s.sort_values("snapshot").groupby(["date", "grade", "brand"]).last().price.unstack(["grade", "brand"])
    days = pd.date_range(last.index.min(), last.index.max(), freq="D")
    daily = last.reindex(days).ffill()
    daily.index.name = "date"
    long = daily.stack(["grade", "brand"], future_stack=True).rename("price").dropna().reset_index()
    long.to_csv(ROOT / "data/hk_daily.csv", index=False)
    print(len(long), "brand-grade-days,", long.date.min().date(), "to", long.date.max().date())


if __name__ == "__main__":
    main()
