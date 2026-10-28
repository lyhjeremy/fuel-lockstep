"""Compact chart data for the site: assets/data.json. Every value comes from data/ or results/."""
import json, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA, RES = ROOT / "data", ROOT / "results"
BRANDS = ["Caltex", "Esso", "PetroChina", "Shell", "Sinopec"]


def r2(x):
    return None if pd.isna(x) else round(float(x), 2)


def main():
    h = pd.read_csv(DATA / "hk_daily.csv", parse_dates=["date"])
    w = h[h.grade == "standard"].pivot(index="date", columns="brand", values="price")[BRANDS]
    start = w.index.min()
    # Step series stored as change points: [day offset, price].
    steps = {}
    for b in BRANDS:
        s = w[b]
        ch = s[s.ne(s.shift())]
        steps[b] = [[int((d - start).days), r2(v)] for d, v in ch.items()]

    m = pd.read_csv(RES / "hk_margin_monthly.csv")
    margin = [[r.month[:7], r2(r.posted), r2(r["import"]), r2(r.duty), r2(r.margin)] for _, r in m.iterrows()]

    nm = pd.read_csv(RES / "hk_net_margin.csv")
    disc = pd.read_csv(DATA / "hk_walkin_discounts.csv")
    disc = disc[disc.grade == "standard"]
    net_by_day = disc.pivot_table(index="date", columns="brand", values="net")
    net = []
    for _, r in nm.iterrows():
        row = net_by_day.loc[r.date] if r.date in net_by_day.index else None
        net.append([r.date, r2(r.posted), r2(r.net_mean), r2(r.net_min), r2(r.import_hkd_per_l),
                    {b: r2(row[b]) for b in BRANDS if row is not None and b in row and pd.notna(row[b])}])

    ep = pd.read_csv(RES / "hk_episodes.csv")
    ep = ep[ep.grade == "standard"]
    episodes = [[r.start, r.direction, r2(r["size"]), r.leaders, [None if pd.isna(r[f"lag_{b}"]) else int(r[f"lag_{b}"]) for b in BRANDS]]
                for _, r in ep.iterrows()]

    irf = pd.read_csv(RES / "passthrough_irf.csv")
    pt = {mk: {"rise": g.rise.round(3).tolist(), "fall": g.fall.round(3).tolist()} for mk, g in irf.groupby("market", sort=False)}

    p = pd.read_csv(RES / "perth_daily.csv")
    perth = [[r.date, int(r.stations), r2(r["min"]), r2(r.p10), r2(r.p25), r2(r["median"]), r2(r.p75), r2(r.p90), r2(r["max"])] for _, r in p.iterrows()]

    by = pd.read_csv(RES / "hk_by_year.csv")
    summary = json.loads((RES / "summary.json").read_text())

    out = {
        "brands": BRANDS,
        "hkStart": start.strftime("%Y-%m-%d"),
        "hkDays": int((w.index.max() - start).days) + 1,
        "steps": steps,
        "margin": margin,
        "net": net,
        "episodes": episodes,
        "passthrough": pt,
        "passthroughSummary": summary["passthrough"],
        "perth": perth,
        "perthDow": summary["perth"]["dow_median_cents"],
        "byYear": by.round(4).to_dict(orient="records"),
        "numbers": json.loads((ROOT / "site/numbers.json").read_text()),
    }
    (ROOT / "assets").mkdir(exist_ok=True)
    (ROOT / "assets/data.json").write_text(json.dumps(out, separators=(",", ":")))
    print("assets/data.json", round((ROOT / "assets/data.json").stat().st_size / 1024), "KB")


if __name__ == "__main__":
    main()
