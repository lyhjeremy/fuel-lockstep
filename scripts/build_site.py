"""Fill the page, write-up fragment and README templates from site/numbers.json; copy the paper PDF."""
import json, pathlib, re, shutil

ROOT = pathlib.Path(__file__).resolve().parent.parent


def main():
    n = json.loads((ROOT / "site/numbers.json").read_text())
    t = (ROOT / "site/index.template.html").read_text()
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", t)) - set(n))
    if missing:
        raise SystemExit(f"numbers missing: {missing}")
    html = re.sub(r"\{\{(\w+)\}\}", lambda m: str(n[m.group(1)]), t)
    (ROOT / "index.html").write_text(html)
    frag = (ROOT / "site/overview.fragment.html").read_text()
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", frag)) - set(n))
    if missing:
        raise SystemExit(f"numbers missing in fragment: {missing}")
    frag = re.sub(r"\{\{(\w+)\}\}", lambda m: str(n[m.group(1)]), frag)
    tooling = ROOT.parent.parent / "_ai-projects-tooling/overview-pages/fragments/fuel-lockstep.html"
    if tooling.parent.exists():
        tooling.write_text(frag)
    readme = (ROOT / "site/README.template.md").read_text()
    missing = sorted(set(re.findall(r"\{\{(\w+)\}\}", readme)) - set(n))
    if missing:
        raise SystemExit(f"numbers missing in README: {missing}")
    (ROOT / "README.md").write_text(re.sub(r"\{\{(\w+)\}\}", lambda m: str(n[m.group(1)]), readme))
    pdf = ROOT / "paper/main.pdf"
    if pdf.exists():
        shutil.copy(pdf, ROOT / "paper/fuel-lockstep.pdf")
    print("index.html written")


if __name__ == "__main__":
    main()
