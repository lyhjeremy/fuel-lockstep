"""Download EIA price series (no API key needed) into data/eia.csv.

Retail series are weekly (Monday); spot series are daily.
"""
import io, pathlib, urllib.request
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
BASE = "https://www.eia.gov/dnav/pet/hist_xls/{}.xls"
SERIES = {
    "la_retail": "EMM_EPMR_PTE_Y05LA_DPGw",   # Los Angeles regular, all formulations, $/gal
    "ca_retail": "EMM_EPMR_PTE_SCA_DPGw",     # California regular, all formulations, $/gal
    "us_retail": "EMM_EPMRU_PTE_NUS_DPGw",    # US regular conventional, $/gal
    "la_spot": "EER_EPMRR_PF4_Y05LA_DPGd",    # Los Angeles reformulated RBOB regular spot, $/gal
    "gc_spot": "EER_EPMRU_PF4_RGC_DPGd",      # US Gulf Coast conventional regular spot, $/gal
    "brent": "RBRTEd",                        # Brent spot FOB, $/bbl
}


def main():
    frames = []
    for name, code in SERIES.items():
        raw = urllib.request.urlopen(BASE.format(code), timeout=120).read()
        d = pd.read_excel(io.BytesIO(raw), sheet_name="Data 1", skiprows=2)
        d.columns = ["date", "value"]
        d["series"] = name
        frames.append(d.dropna())
    out = pd.concat(frames)
    out["date"] = pd.to_datetime(out.date).dt.date
    out.to_csv(ROOT / "data/eia.csv", index=False)
    print(out.groupby("series").date.agg(["min", "max", "count"]))


if __name__ == "__main__":
    main()
