"""Asymmetric cost pass-through (the "rockets and feathers" test).

Error-correction model in the spirit of Borenstein, Cameron and Gilbert (1997):

    d r_t = a + sum_k (b+_k d x+_{t-k} + b-_k d x-_{t-k}) + sum_j f_j d r_{t-j} + g (r_{t-1} - c - t x_{t-1}) + e_t

r is the retail price, x the cost, both in the same currency per litre. d x+ keeps cost rises
and d x- keeps cost falls. The long-run relation r = c + t x is estimated first in levels.
Responses to a permanent one-unit cost rise and fall are found by simulating the fitted model.
"""
import numpy as np
import pandas as pd
import statsmodels.api as sm


def fit(r: pd.Series, x: pd.Series, k: int = 6, j: int = 2, trend: bool = False):
    """trend=True adds a linear time trend to the long-run relation, for a margin that drifts."""
    df = pd.concat({"r": r, "x": x}, axis=1).dropna()
    levels = df[["x"]].assign(t=np.arange(len(df))) if trend else df[["x"]]
    lr = sm.OLS(df.r, sm.add_constant(levels)).fit()
    ect = (df.r - lr.fittedvalues).shift(1)
    dx, dr = df.x.diff(), df.r.diff()
    cols = {}
    for i in range(k + 1):
        cols[f"up{i}"] = dx.clip(lower=0).shift(i)
        cols[f"dn{i}"] = dx.clip(upper=0).shift(i)
    for i in range(1, j + 1):
        cols[f"ar{i}"] = dr.shift(i)
    cols["ect"] = ect
    X = sm.add_constant(pd.DataFrame(cols))
    data = pd.concat([dr.rename("dr"), X], axis=1).dropna()
    m = sm.OLS(data.dr, data.drop(columns="dr")).fit(cov_type="HAC", cov_kwds={"maxlags": k})
    return {"long_run": lr, "model": m, "k": k, "j": j, "n": int(m.nobs)}


def response(res, sign: int, horizon: int = 12):
    """Cumulative retail response to a permanent cost step of +1 (sign=1) or -1 (sign=-1)."""
    p, k, j = res["model"].params, res["k"], res["j"]
    theta = res["long_run"].params["x"]
    steps = horizon + 1
    dx = np.zeros(steps)
    dx[0] = sign
    x = np.cumsum(dx)
    r = np.zeros(steps)
    dr = np.zeros(steps)
    for t in range(steps):
        v = 0.0
        for i in range(k + 1):
            if t - i >= 0:
                key = "up" if dx[t - i] > 0 else "dn"
                v += p[f"{key}{i}"] * dx[t - i]
        for i in range(1, j + 1):
            if t - i >= 0:
                v += p[f"ar{i}"] * dr[t - i]
        prev_r = r[t - 1] if t else 0.0
        prev_x = x[t - 1] if t else 0.0
        v += p["ect"] * (prev_r - theta * prev_x)
        dr[t] = v
        r[t] = prev_r + v
    return r * sign  # share of the step passed through, positive for both directions


def asymmetry_test(res, upto: int = 2):
    """Wald test that cumulative pass-through of rises equals that of falls over lags 0..upto."""
    m = res["model"]
    names = list(m.params.index)
    w = np.zeros(len(names))
    for i in range(upto + 1):
        w[names.index(f"up{i}")] += 1
        w[names.index(f"dn{i}")] -= 1
    t = m.t_test(w)
    return {"diff": float(t.effect[0]), "se": float(t.sd[0][0]), "p": float(t.pvalue)}
