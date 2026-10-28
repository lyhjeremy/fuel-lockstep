"""Run every screen and write results/*.csv and results/summary.json.

Inputs (all in data/): hk_daily.csv, hk_import_unit_value.csv, eia.csv, fx.csv, wa_perth_ulp.csv.gz.
"""
import json, pathlib, sys
import numpy as np
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from analysis import lockstep as ls, passthrough as pt  # noqa: E402

DATA, OUT = ROOT / "data", ROOT / "results"
LITRES_PER_GALLON = 3.785411784
HK_PETROL_DUTY = 6.06  # HK$ per litre, unchanged since 1998 (Consumer Council explanatory note)
BRANDS_HK = ["Caltex", "Esso", "PetroChina", "Shell", "Sinopec"]


def load():
    hk = pd.read_csv(DATA / "hk_daily.csv", parse_dates=["date"])
    imp = pd.read_csv(DATA / "hk_import_unit_value.csv")
    eia = pd.read_csv(DATA / "eia.csv", parse_dates=["date"]).pivot(index="date", columns="series", values="value")
    fx = pd.read_csv(DATA / "fx.csv", parse_dates=["date"]).pivot(index="date", columns="series", values="value")
    wa = pd.read_csv(DATA / "wa_perth_ulp.csv.gz", parse_dates=["date"])
    return hk, imp, eia, fx, wa


def weekly_mean_before(daily: pd.Series) -> pd.Series:
    """Mean over the seven days before each Monday, labeled with that Monday."""
    return daily.resample("W-MON", label="right", closed="left").mean()


def hk_screens(hk):
    out, ep_all = {}, []
    for g in ["standard", "premium", "diesel"]:
        w = hk[hk.grade == g].pivot(index="date", columns="brand", values="price")[BRANDS_HK]
        a = ls.alignment(w)
        e = ls.episodes(w)
        e["grade"] = g
        ep_all.append(e)
        full = e[e.n_within_window == 5]
        out[g] = {
            "days": len(a),
            "share_days_all_equal": round(float(a.all_equal.mean()), 4),
            "median_range_when_unequal": round(float(a.loc[~a.all_equal, "range"].median()), 2) if (~a.all_equal).any() else 0.0,
            "episodes": len(e),
            "episodes_up": int((e.direction == "up").sum()),
            "episodes_down": int((e.direction == "down").sum()),
            "share_all_five_within_7d": round(float((e.n_within_window == 5).mean()), 4),
            "share_all_five_same_day": round(float((e.n_same_day == 5).mean()), 4),
            "share_full_episodes_same_size": round(float(full.same_size.mean()), 4),
            "median_max_lag_days_full": float(full.max_lag_days.median()),
            "median_size_up": float(e.loc[e.direction == "up", "size"].median()),
            "median_size_down": float(e.loc[e.direction == "down", "size"].median()),
            "leaders_single": e.loc[e.n_same_day == 1, "leaders"].value_counts().to_dict(),
            "by_year_all_equal": a.all_equal.groupby(a.index.year).mean().round(4).to_dict(),
        }
    pd.concat(ep_all).to_csv(OUT / "hk_episodes.csv", index=False)
    return out


def hk_posted(hk, grade="standard"):
    """Modal posted price across the five brands each day."""
    w = hk[hk.grade == grade].pivot(index="date", columns="brand", values="price")
    return w.mode(axis=1)[0]


def hk_margin(hk, imp):
    p = hk_posted(hk).resample("MS").mean()
    m = imp.assign(month=pd.to_datetime(imp.month)).set_index("month").import_hkd_per_l
    df = pd.concat({"posted": p, "import": m}, axis=1).dropna()
    df["duty"] = HK_PETROL_DUTY
    df["margin"] = df.posted - df.duty - df["import"]
    df.round(3).to_csv(OUT / "hk_margin_monthly.csv", index_label="month")
    return df


def hk_net_margin(imp):
    """Margin over import cost and duty on the average net price after walk-in discounts (archived days only)."""
    d = pd.read_csv(DATA / "hk_walkin_discounts.csv", parse_dates=["date"])
    d = d[d.grade == "standard"]
    day = d.groupby("date").agg(posted=("pump", "max"), net_mean=("net", "mean"), net_min=("net", "min"),
                                discount_mean=("walkin_discount", "mean"), discount_max=("walkin_discount", "max")).reset_index()
    day["month"] = day.date.dt.to_period("M").dt.to_timestamp()
    im = imp.assign(month=pd.to_datetime(imp.month))[["month", "import_hkd_per_l"]]
    day = day.merge(im, on="month", how="inner")
    day["posted_margin"] = day.posted - HK_PETROL_DUTY - day.import_hkd_per_l
    day["net_margin"] = day.net_mean - HK_PETROL_DUTY - day.import_hkd_per_l
    day.drop(columns="month").round(3).to_csv(OUT / "hk_net_margin.csv", index=False)
    first = day[day.date < day.date.min() + pd.Timedelta(days=365)]
    last = day[day.date > day.date.max() - pd.Timedelta(days=365)]
    cols = ["posted", "net_mean", "discount_mean", "import_hkd_per_l", "posted_margin", "net_margin"]
    return {"days": len(day), "first_year_days": len(first), "last_year_days": len(last),
            "first_year": first[cols].mean().round(2).to_dict(), "last_year": last[cols].mean().round(2).to_dict()}


def to_local_per_litre(usd_per_gal: pd.Series, rate: pd.Series) -> pd.Series:
    rate = rate.reindex(usd_per_gal.index).ffill().bfill()
    return usd_per_gal * rate / LITRES_PER_GALLON


def passthrough_summary(name, r, x, k=4, j=1, horizon=12, trend=False):
    res = pt.fit(r, x, k=k, j=j, trend=trend)
    up, dn = pt.response(res, 1, horizon), pt.response(res, -1, horizon)
    asym = pt.asymmetry_test(res, upto=1)
    rows = pd.DataFrame({"market": name, "week": range(horizon + 1), "rise": up.round(4), "fall": dn.round(4)})
    return rows, {
        "n_weeks": res["n"],
        "start": str(r.dropna().index.min().date()),
        "end": str(r.dropna().index.max().date()),
        "long_run_slope": round(float(res["long_run"].params["x"]), 3),
        "long_run_trend_per_year": round(float(res["long_run"].params.get("t", 0.0)) * 52, 3),
        "ect": round(float(res["model"].params["ect"]), 3),
        "week0_rise": round(float(up[0]), 3),
        "week0_fall": round(float(dn[0]), 3),
        "week4_rise": round(float(up[4]), 3),
        "week4_fall": round(float(dn[4]), 3),
        "asym_weeks01_diff": round(asym["diff"], 3),
        "asym_weeks01_p": round(asym["p"], 4),
    }


def perth_daily(wa):
    g = wa.groupby("date").price_cents_l
    d = pd.DataFrame({
        "stations": g.size(),
        "median": g.median(),
        "p10": g.quantile(0.10),
        "p25": g.quantile(0.25),
        "p75": g.quantile(0.75),
        "p90": g.quantile(0.90),
        "min": g.min(),
        "max": g.max(),
        "modal_share": g.agg(lambda x: (x == x.mode().iloc[0]).mean()),
    })
    d["iqr"] = d.p75 - d.p25
    d["range"] = d["max"] - d["min"]
    d.round(3).to_csv(OUT / "perth_daily.csv", index_label="date")
    return d


def perth_brands(wa):
    """Daily median by brand for the largest brands, and how often they match."""
    top = wa.brand.value_counts().head(8).index
    b = wa[wa.brand.isin(top)].groupby(["date", "brand"]).price_cents_l.median().unstack()
    b.round(2).to_csv(OUT / "perth_brand_medians.csv", index_label="date")
    a = ls.alignment(b)
    return {"brands": list(top), "share_days_all_brand_medians_equal": round(float(a.all_equal.mean()), 4),
            "median_brand_range_cents": round(float(a.range.median()), 2)}


def main():
    OUT.mkdir(exist_ok=True)
    hk, imp, eia, fx, wa = load()
    s = {"hk": hk_screens(hk)}

    m = hk_margin(hk, imp)
    s["hk_margin"] = {
        "months": len(m), "start": str(m.index.min().date()), "end": str(m.index.max().date()),
        "mean_import": round(float(m["import"].mean()), 2), "mean_margin": round(float(m.margin.mean()), 2),
        "margin_first12": round(float(m.margin.iloc[:12].mean()), 2), "margin_last12": round(float(m.margin.iloc[-12:].mean()), 2),
        "posted_first12": round(float(m.posted.iloc[:12].mean()), 2), "posted_last12": round(float(m.posted.iloc[-12:].mean()), 2),
        "import_first12": round(float(m["import"].iloc[:12].mean()), 2), "import_last12": round(float(m["import"].iloc[-12:].mean()), 2),
    }

    s["hk_net_margin"] = hk_net_margin(imp)

    # Weekly pass-through, every market against a gasoline spot price in local currency per litre.
    gc_hkd = to_local_per_litre(eia.gc_spot.dropna(), fx.hkd_per_usd.dropna())
    gc_aud = to_local_per_litre(eia.gc_spot.dropna(), 1 / fx.usd_per_aud.dropna())
    hk_daily_posted = hk_posted(hk)
    hk_week = hk_daily_posted[hk_daily_posted.index.dayofweek == 0]  # Monday price, matching the EIA survey day
    la_cost = weekly_mean_before(eia.la_spot.dropna()) / LITRES_PER_GALLON * 100  # US cents per litre
    la_retail = eia.la_retail.dropna() / LITRES_PER_GALLON * 100
    la_retail = la_retail[la_retail.index >= hk_week.index.min()]
    pd_ = perth_daily(wa)
    # Perth prices cycle within the week, so sample one point of the cycle: the Tuesday trough.
    perth_week = pd_["median"][pd_.index.dayofweek == 1].resample("W-MON", label="right", closed="left").last()

    rows, s["passthrough"] = [], {}
    for name, r, x, trend in [
        ("Hong Kong", hk_week, weekly_mean_before(gc_hkd), True),
        ("Los Angeles", la_retail, la_cost, False),
        ("Perth", perth_week, weekly_mean_before(gc_aud) * 100, False),
    ]:
        df, summ = passthrough_summary(name, r, x, trend=trend)
        rows.append(df)
        s["passthrough"][name] = summ
    pd.concat(rows).to_csv(OUT / "passthrough_irf.csv", index=False)

    # Robustness: every market under other lag lengths and, for Perth, other points of the cycle.
    perth_alt = {
        "Perth (weekly mean)": pd_["median"].resample("W-MON", label="right", closed="left").mean(),
        "Perth (Wednesday peak)": pd_["median"][pd_.index.dayofweek == 2].resample("W-MON", label="right", closed="left").last(),
    }
    rob = []
    specs = [("Hong Kong", hk_week, weekly_mean_before(gc_hkd), True), ("Los Angeles", la_retail, la_cost, False),
             ("Perth", perth_week, weekly_mean_before(gc_aud) * 100, False)]
    specs += [(n, r, weekly_mean_before(gc_aud) * 100, False) for n, r in perth_alt.items()]
    for name, r, x, trend in specs:
        for k, j in [(4, 1), (6, 2), (8, 2)]:
            res = pt.fit(r, x, k=k, j=j, trend=trend)
            up, dn = pt.response(res, 1, 12), pt.response(res, -1, 12)
            a = pt.asymmetry_test(res, upto=1)
            rob.append({"market": name, "cost_lags": k, "retail_lags": j, "rise_w0": up[0], "fall_w0": dn[0],
                        "rise_w4": up[4], "fall_w4": dn[4], "rise_w12": up[12], "fall_w12": dn[12],
                        "asym_w01": a["diff"], "asym_p": a["p"], "n": res["n"]})
    pd.DataFrame(rob).round(3).to_csv(OUT / "passthrough_robustness.csv", index=False)

    # Weekly series for the variance screen and the site's price chart.
    wk = pd.concat({
        "hk_posted_hkd_l": hk_week, "hk_cost_hkd_l": weekly_mean_before(gc_hkd),
        "la_retail_usc_l": la_retail, "la_cost_usc_l": la_cost,
        "perth_tuesday_ausc_l": perth_week, "perth_cost_ausc_l": weekly_mean_before(gc_aud) * 100,
    }, axis=1)
    wk = wk[wk.index >= hk_week.index.min()]
    wk.round(4).to_csv(OUT / "weekly.csv", index_label="week")

    vs = {}
    for mkt, r, c in [("Hong Kong", "hk_posted_hkd_l", "hk_cost_hkd_l"), ("Los Angeles", "la_retail_usc_l", "la_cost_usc_l"), ("Perth", "perth_tuesday_ausc_l", "perth_cost_ausc_l")]:
        d = wk[[r, c]].dropna()
        dr, dc = d[r].diff(), d[c].diff()
        vs[mkt] = {
            "sd_weekly_change_retail_over_cost": round(float(dr.std() / dc.std()), 3),
            "share_weeks_retail_unchanged": round(float((dr.round(4) == 0).mean()), 4),
            "corr_level_retail_cost": round(float(d[r].corr(d[c])), 3),
        }
    s["variance_screen"] = vs

    # Hong Kong by year: does alignment loosen when costs move more?
    hk_std = hk[hk.grade == "standard"].pivot(index="date", columns="brand", values="price")
    al = ls.alignment(hk_std)
    ep = pd.read_csv(OUT / "hk_episodes.csv", parse_dates=["start"])
    ep = ep[ep.grade == "standard"]
    cost_w = weekly_mean_before(gc_hkd)
    by = pd.DataFrame({
        "share_days_all_equal": al.all_equal.groupby(al.index.year).mean(),
        "days": al.all_equal.groupby(al.index.year).size(),
        "episodes": ep.groupby(ep.start.dt.year).size(),
        "episodes_up": ep[ep.direction == "up"].groupby(ep[ep.direction == "up"].start.dt.year).size(),
        "cost_sd_weekly_change_hkd_l": cost_w.diff().groupby(cost_w.index.year).std(),
    }).loc[2020:].fillna(0)
    by.round(4).to_csv(OUT / "hk_by_year.csv", index_label="year")
    s["hk_by_year_corr_cost_sd_vs_all_equal"] = round(float(by.cost_sd_weekly_change_hkd_l.corr(by.share_days_all_equal)), 3)

    s["perth"] = {
        "days": len(pd_), "start": str(pd_.index.min().date()), "end": str(pd_.index.max().date()),
        "mean_stations": round(float(pd_.stations.mean()), 1),
        "median_daily_range_cents": round(float(pd_.range.median()), 2),
        "median_daily_iqr_cents": round(float(pd_.iqr.median()), 2),
        "median_modal_share": round(float(pd_.modal_share.median()), 4),
        "dow_median_cents": pd_["median"].groupby(pd_.index.day_name()).mean().round(2).to_dict(),
        **perth_brands(wa),
    }
    (OUT / "summary.json").write_text(json.dumps(s, indent=2, default=str))
    print(json.dumps(s, indent=2, default=str))


if __name__ == "__main__":
    main()
