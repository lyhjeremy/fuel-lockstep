"""Write every number the paper and site quote into paper/numbers.tex and site/numbers.json.

The text never types a result by hand; it uses these macros, so a rerun of the analysis
updates the paper and the site together.
"""
import json, pathlib
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES = ROOT / "results"


def pct(x, d=0):
    return f"{100 * x:.{d}f}"


def build():
    s = json.loads((RES / "summary.json").read_text())
    st = s["hk"]["standard"]
    m = pd.read_csv(RES / "hk_margin_monthly.csv", parse_dates=["month"]).set_index("month")
    by = pd.read_csv(RES / "hk_by_year.csv").set_index("year")
    span = m.loc["2023-01":"2025-12"]
    pt_ = s["passthrough"]
    n = {
        "hkDays": f"{st['days']:,}",
        "hkStart": "30 April 2020",
        "hkShareEqual": pct(st["share_days_all_equal"], 1),
        "hkEpisodes": st["episodes"],
        "hkEpisodesUp": st["episodes_up"],
        "hkEpisodesDown": st["episodes_down"],
        "hkShareFullWeek": pct(st["share_all_five_within_7d"]),
        "hkShareSameDay": pct(st["share_all_five_same_day"], 1),
        "hkShareSameSize": pct(st["share_full_episodes_same_size"]),
        "hkMedianLag": f"{st['median_max_lag_days_full']:.0f}",
        "hkSizeUp": f"{st['median_size_up']:.2f}",
        "hkSizeDown": f"{abs(st['median_size_down']):.2f}",
        "hkLeadShell": st["leaders_single"].get("Shell", 0),
        "hkLeadEsso": st["leaders_single"].get("Esso", 0),
        "hkLeadCaltex": st["leaders_single"].get("Caltex", 0),
        "hkLeadSingle": sum(st["leaders_single"].values()),
        "hkEqualTwentyThree": pct(by.loc[2023, "share_days_all_equal"]),
        "hkEqualTwentySix": pct(by.loc[2026, "share_days_all_equal"]),
        "hkUpTwentyThreeFour": int(by.loc[2023, "episodes_up"] + by.loc[2024, "episodes_up"]),
        "hkDownTwentyThreeFour": (lambda v: "no" if v == 0 else v)(int(by.loc[2023, "episodes"] - by.loc[2023, "episodes_up"] + by.loc[2024, "episodes"] - by.loc[2024, "episodes_up"])),
        "postedFirst": f"{s['hk_margin']['posted_first12']:.2f}",
        "postedLast": f"{s['hk_margin']['posted_last12']:.2f}",
        "importFirst": f"{s['hk_margin']['import_first12']:.2f}",
        "importLast": f"{s['hk_margin']['import_last12']:.2f}",
        "marginFirst": f"{s['hk_margin']['margin_first12']:.2f}",
        "marginLast": f"{s['hk_margin']['margin_last12']:.2f}",
        "marginEnd": s["hk_margin"]["end"][:7],
        "spanPostedFrom": f"{span.posted.iloc[0]:.2f}",
        "spanPostedTo": f"{span.posted.iloc[-1]:.2f}",
        "spanImportFrom": f"{span['import'].iloc[0]:.2f}",
        "spanImportTo": f"{span['import'].iloc[-1]:.2f}",
        "hkTrendYear": f"{pt_['Hong Kong']['long_run_trend_per_year']:.2f}",
        "perthStations": f"{s['perth']['mean_stations']:.0f}",
        "perthRange": f"{s['perth']['median_daily_range_cents']:.0f}",
        "perthIqr": f"{s['perth']['median_daily_iqr_cents']:.0f}",
        "perthModal": pct(s["perth"]["median_modal_share"]),
        "perthTue": f"{s['perth']['dow_median_cents']['Tuesday']:.1f}",
        "perthWed": f"{s['perth']['dow_median_cents']['Wednesday']:.1f}",
        "perthBrandRange": f"{s['perth']['median_brand_range_cents']:.1f}",
        "hkUnchangedWeeks": pct(s["variance_screen"]["Hong Kong"]["share_weeks_retail_unchanged"]),
        "laUnchangedWeeks": pct(s["variance_screen"]["Los Angeles"]["share_weeks_retail_unchanged"], 1),
        "perthUnchangedWeeks": pct(s["variance_screen"]["Perth"]["share_weeks_retail_unchanged"]),
    }
    for mk, key in [("Hong Kong", "hk"), ("Los Angeles", "la"), ("Perth", "perth")]:
        p = pt_[mk]
        n[f"{key}RiseZero"] = pct(p["week0_rise"])
        n[f"{key}FallZero"] = pct(p["week0_fall"])
        n[f"{key}RiseFour"] = pct(p["week4_rise"])
        n[f"{key}FallFour"] = pct(p["week4_fall"])
        n[f"{key}AsymP"] = f"{p['asym_weeks01_p']:.3f}"
        n[f"{key}Weeks"] = p["n_weeks"]
    f = ROOT / "data/hk_walkin_discounts.csv"
    if f.exists():
        d = pd.read_csv(f, parse_dates=["date"])
        d = d[d.grade == "standard"]
        first, last = d.date.min(), d.date.max()
        g = d.groupby("date")
        n["discDays"] = d.date.nunique()
        n["discFirst"] = first.strftime("%-d %B %Y")
        n["discLast"] = last.strftime("%-d %B %Y")
        n["discMaxFirst"] = f"{g.walkin_discount.max().loc[first]:.2f}"
        n["discMaxLast"] = f"{g.walkin_discount.max().loc[last]:.2f}"
        n["discNetMinFirst"] = f"{g.net.min().loc[first]:.2f}"
        n["discNetMinLast"] = f"{g.net.min().loc[last]:.2f}"
        n["discPumpFirst"] = f"{g.pump.max().loc[first]:.2f}"
        n["discPumpLast"] = f"{g.pump.max().loc[last]:.2f}"
    hm = s["hk_margin"]
    n["postedRise"] = f"{hm['posted_last12'] - hm['posted_first12']:.2f}"
    n["importRise"] = f"{hm['import_last12'] - hm['import_first12']:.2f}"
    n["marginRise"] = f"{hm['margin_last12'] - hm['margin_first12']:.2f}"
    n["marginShareOfRise"] = pct((hm['margin_last12'] - hm['margin_first12']) / (hm['posted_last12'] - hm['posted_first12']))
    n["discMatch"] = pct(s["discount_crosscheck_match_share"], 1)
    n["hkPartial"] = s["hk_partial"]["partial_episodes"]
    n["hkLone"] = s["hk_partial"]["lone_unfollowed"]
    n["hkLoneReversed"] = s["hk_partial"]["lone_reversed_14d"]
    nm = s.get("hk_net_margin")
    if nm:
        for tag, k in [("First", "first_year"), ("Last", "last_year")]:
            n[f"netMargin{tag}"] = f"{nm[k]['net_margin']:.2f}"
            n[f"postedMargin{tag}"] = f"{nm[k]['posted_margin']:.2f}"
            n[f"netMean{tag}"] = f"{nm[k]['net_mean']:.2f}"
            n[f"discMean{tag}"] = f"{nm[k]['discount_mean']:.2f}"
    return n


def main():
    n = build()
    tex = ["% Generated by scripts/export_numbers.py. Do not edit."]
    tex += [f"\\newcommand{{\\{k}}}{{{v}}}" for k, v in n.items()]
    (ROOT / "paper").mkdir(exist_ok=True)
    (ROOT / "paper/numbers.tex").write_text("\n".join(tex) + "\n")
    (ROOT / "site").mkdir(exist_ok=True)
    (ROOT / "site/numbers.json").write_text(json.dumps(n, indent=1, default=str))
    print(len(n), "numbers")


if __name__ == "__main__":
    main()
