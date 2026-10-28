"""Paper exhibits (vector PDF) from results/ and data/. Ledger base palette, one axis per chart."""
import json, pathlib
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
RES, DATA, OUT = ROOT / "results", ROOT / "data", ROOT / "paper/figures"
OXIDE, PINE, INK, INK2, RULE, GRAY = "#8C3A1E", "#2C5852", "#1C1E1B", "#52564E", "#C6C7BF", "#9A9D94"
BRANDS = ["Caltex", "Esso", "PetroChina", "Shell", "Sinopec"]

plt.rcParams.update({
    "font.family": "serif", "font.serif": ["Source Serif 4", "Source Serif Pro", "Georgia", "DejaVu Serif"],
    "font.size": 9, "axes.edgecolor": INK2, "axes.labelcolor": INK2, "xtick.color": INK2, "ytick.color": INK2,
    "axes.spines.top": False, "axes.spines.right": False, "axes.grid": True, "grid.color": RULE,
    "grid.linewidth": 0.5, "axes.axisbelow": True, "axes.titlesize": 10, "axes.titleweight": "bold",
    "axes.titlelocation": "left", "figure.dpi": 150, "savefig.bbox": "tight", "pdf.fonttype": 42,
})


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{name}.pdf")
    fig.savefig(OUT / f"{name}.png", dpi=200, facecolor="#F5F5F0")  # web copy on the Ledger panel color
    plt.close(fig)


def ex_decomposition():
    m = pd.read_csv(RES / "hk_margin_monthly.csv", parse_dates=["month"]).set_index("month")
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    ax.stackplot(m.index, m["import"], m.duty, m.margin, colors=[PINE, GRAY, OXIDE], alpha=0.9, edgecolor="white", linewidth=0.6)
    last = m.index[-1]
    for y, label in [(m["import"].iloc[-1] / 2, "Import cost"), (m["import"].iloc[-1] + m.duty.iloc[-1] / 2, "Duty (6.06)"),
                     (m["import"].iloc[-1] + m.duty.iloc[-1] + m.margin.iloc[-1] / 2, "Margin over import cost and duty")]:
        ax.annotate(label, (last, y), xytext=(6, 0), textcoords="offset points", va="center", fontsize=8, color=INK)
    ax.set_ylabel("HK$ per litre")
    ax.set_title("Posted Standard price, monthly mean, split into import cost, duty and margin")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    ax.set_xlim(m.index[0], m.index[-1])
    save(fig, "ex1_hk_decomposition")


def ex_posted_steps():
    h = pd.read_csv(DATA / "hk_daily.csv", parse_dates=["date"])
    w = h[h.grade == "standard"].pivot(index="date", columns="brand", values="price")
    w = w.loc["2026-02-01":"2026-05-31"]
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    for b in BRANDS:
        ax.step(w.index, w[b], where="post", color=OXIDE if b == "Shell" else GRAY, lw=1.6 if b == "Shell" else 1.0, label=b)
    ax.annotate("Shell", (w.index[-1], w.Shell.iloc[-1]), xytext=(4, 0), textcoords="offset points", color=INK, fontsize=8, va="center")
    ax.annotate("other four brands", (w.index[-1], w.Caltex.iloc[-1]), xytext=(4, -9), textcoords="offset points", color=INK2, fontsize=8, va="center")
    ax.set_ylabel("HK$ per litre")
    ax.set_title("Posted Standard price by brand, February to May 2026")
    ax.xaxis.set_major_locator(mdates.MonthLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %Y"))
    save(fig, "ex2_hk_steps")


def ex_lags():
    e = pd.read_csv(RES / "hk_episodes.csv", parse_dates=["start"])
    e = e[(e.grade == "standard") & (e.n_within_window == 5)]
    fig, ax = plt.subplots(figsize=(6.5, 3.2))
    for i, b in enumerate(BRANDS):
        lag = e[f"lag_{b}"].value_counts().sort_index()
        for d, n in lag.items():
            ax.scatter(d, i, s=12 + n * 6, color=OXIDE if d == 0 else GRAY, edgecolor="white", linewidth=0.6, zorder=3)
            ax.annotate(str(n), (d, i), xytext=(0, 13), textcoords="offset points", ha="center", fontsize=7, color=INK2)
    ax.set_yticks(range(len(BRANDS)), BRANDS)
    ax.set_xlabel("Days after the first brand moved")
    ax.set_xticks(range(0, 8))
    ax.set_title("When each brand matched a change: count of episodes by lag")
    ax.set_ylim(-0.6, len(BRANDS) - 0.2)
    save(fig, "ex3_hk_lags")


def ex_discounts():
    f = DATA / "hk_walkin_discounts.csv"
    if not f.exists():
        return
    d = pd.read_csv(f, parse_dates=["date"])
    d = d[d.grade == "standard"]
    fig, ax = plt.subplots(figsize=(6.5, 3.0))
    piv = d.pivot_table(index="date", columns="brand", values="net")
    pump = d.groupby("date").pump.max()
    ax.plot(pump.index, pump, color=OXIDE, lw=1.6, marker="o", ms=2.5)
    ax.annotate("Posted price", (pump.index[-1], pump.iloc[-1]), xytext=(4, 0), textcoords="offset points", fontsize=8, va="center")
    lo, hi = piv.min(axis=1), piv.max(axis=1)
    ax.fill_between(piv.index, lo, hi, color=PINE, alpha=0.25, lw=0)
    ax.plot(piv.index, lo, color=PINE, lw=1.2, ls="--")
    ax.annotate("Cheapest net price\nafter walk-in discount", (piv.index[-1], lo.iloc[-1]), xytext=(4, -4), textcoords="offset points", fontsize=8, va="center")
    ax.annotate("shaded: net price range across the five brands", (0.01, 0.97), xycoords="axes fraction", va="top", fontsize=8, color=INK2)
    ax.set_ylabel("HK$ per litre")
    ax.set_title("Posted price and the range of net prices after walk-in discounts")
    ax.xaxis.set_major_locator(mdates.YearLocator())
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))
    save(fig, "ex4_hk_discounts")


def ex_passthrough():
    irf = pd.read_csv(RES / "passthrough_irf.csv")
    fig, axes = plt.subplots(1, 3, figsize=(6.5, 2.4), sharey=True)
    for ax, (mkt, g) in zip(axes, irf.groupby("market", sort=False)):
        ax.plot(g.week, g.rise, color=OXIDE, lw=1.8)
        ax.plot(g.week, g.fall, color=PINE, lw=1.8, ls="--")
        ax.set_title(mkt, fontsize=9)
        ax.set_xticks([0, 4, 8, 12])
        ax.axhline(1, color=INK2, lw=0.6, ls=":")
        ax.set_xlabel("Weeks after cost change")
        ax.annotate("rise", (12, g.rise.iloc[-1]), xytext=(-2, 5), textcoords="offset points", ha="right", fontsize=8, color=INK)
        ax.annotate("fall", (12, g.fall.iloc[-1]), xytext=(-2, -11), textcoords="offset points", ha="right", fontsize=8, color=INK)
    axes[0].set_ylabel("Share of cost change passed through")
    fig.suptitle("Retail response to a permanent change in gasoline cost", x=0.02, ha="left", fontsize=10, fontweight="bold")
    fig.tight_layout()
    save(fig, "ex5_passthrough")


def ex_perth():
    p = pd.read_csv(RES / "perth_daily.csv", parse_dates=["date"]).set_index("date")
    w = p.loc["2025-06-01":"2025-08-31"]
    fig, ax = plt.subplots(figsize=(6.5, 2.8))
    ax.fill_between(w.index, w.p10, w.p90, color=GRAY, alpha=0.35, lw=0, step="mid")
    ax.step(w.index, w["median"], where="mid", color=OXIDE, lw=1.5)
    ax.annotate("median station", (w.index[-1], w["median"].iloc[-1]), xytext=(4, 0), textcoords="offset points", fontsize=8, va="center")
    ax.annotate("shaded: 10th to 90th percentile of stations", (0.01, 0.97), xycoords="axes fraction", va="top", fontsize=8, color=INK2)
    ax.set_ylabel("Australian cents per litre")
    ax.set_title("Perth unleaded, every metro station, June to August 2025")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d %b"))
    save(fig, "ex6_perth_cycle")


def main():
    for f in [ex_decomposition, ex_posted_steps, ex_lags, ex_discounts, ex_passthrough, ex_perth]:
        f()
        print("ok", f.__name__)


if __name__ == "__main__":
    main()
