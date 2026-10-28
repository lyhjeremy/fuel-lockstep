"""Monthly import unit value and net imports of unleaded petrol, Hong Kong C&SD table 915-91104."""
import json, pathlib, urllib.request
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
URL = "https://www.censtatd.gov.hk/api/get.php?id=915-91104&lang=en&full_series=1"


def main():
    d = pd.DataFrame(json.loads(urllib.request.urlopen(urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0"}), timeout=120).read())["dataSet"])
    d = d[(d.PROD_TYPE.astype(str) == "2b") & (d.freq == "M")]
    d = d[(d.sv == "UNIT_VAL_IM") | (d.svDesc == "Kilolitres")]
    out = d.pivot_table(index="period", columns="sv", values="figure", aggfunc="first").reset_index()
    out.columns = ["month", "net_imports_kl", "import_hkd_per_l"]
    out["month"] = pd.to_datetime(out.month.astype(str), format="%Y%m").dt.strftime("%Y-%m")
    out.to_csv(ROOT / "data/hk_import_unit_value.csv", index=False)
    print(len(out), out.month.min(), out.month.max())


if __name__ == "__main__":
    main()
