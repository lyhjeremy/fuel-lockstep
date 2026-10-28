"""Timing and alignment screens for a small panel of brands with posted prices.

Input is a wide frame: one row per day, one column per brand, the posted price that day.
"""
import numpy as np
import pandas as pd


def alignment(wide: pd.DataFrame) -> pd.DataFrame:
    """Per day: cross-brand range and whether every brand posts the same price."""
    rng = wide.max(axis=1) - wide.min(axis=1)
    return pd.DataFrame({"range": rng.round(4), "all_equal": rng.round(4) == 0, "n_brands": wide.notna().sum(axis=1)})


def changes(wide: pd.DataFrame) -> pd.DataFrame:
    """One row per brand price change: date, brand, size."""
    d = wide.diff()
    out = d.stack().rename("size").reset_index()
    out.columns = ["date", "brand", "size"]
    return out[out["size"].round(4) != 0].reset_index(drop=True)


def episodes(wide: pd.DataFrame, window: int = 7) -> pd.DataFrame:
    """Group changes into episodes started by a first mover.

    An episode opens with the first change after the previous episode closed. It collects each
    other brand's first change in the same direction within `window` days. For each episode we
    record who led, how many brands followed, the follower lags, and whether every brand moved
    by the same amount.
    """
    ch = changes(wide).sort_values(["date", "brand"])
    brands = list(wide.columns)
    rows, used = [], set()
    for idx, c in ch.iterrows():
        if idx in used:
            continue
        start, sign = c.date, np.sign(c["size"])
        pool = ch[(ch.date >= start) & (ch.date <= start + pd.Timedelta(days=window)) & (np.sign(ch["size"]) == sign)]
        pool = pool[~pool.index.isin(used)]
        first = pool.sort_values("date").groupby("brand").head(1)
        used.update(first.index)
        leaders = sorted(first[first.date == start].brand)
        lags = {b: (first.loc[first.brand == b, "date"].iloc[0] - start).days for b in first.brand}
        sizes = first["size"].round(4)
        rows.append({
            "start": start,
            "direction": "up" if sign > 0 else "down",
            "leaders": "+".join(leaders),
            "n_same_day": len(leaders),
            "n_within_window": len(first),
            "max_lag_days": max(lags.values()),
            "same_size": sizes.nunique() == 1,
            "size": float(sizes.median()),
            **{f"lag_{b}": lags.get(b, np.nan) for b in brands},
        })
    return pd.DataFrame(rows)
