"""CLI: parse master -> JSON ; curate request -> .do."""
import argparse
import json
from pathlib import Path

from .parser import parse_master
from .curator import curate, generate_do, generate_readme


def cmd_parse(a):
    data = parse_master(a.xlsx, survey_id=a.survey, period=a.period)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"sheet={data['kamus_sheet']} vars={data['n_variables']} parts={data['partitions']}")
    print(f"mandatory={str(data['mandatory'])[:150]}")
    print(f"-> {out}")


def cmd_curate(a):
    master = json.loads(Path(a.master).read_text(encoding="utf-8"))
    if len(a.req) == 1 and Path(a.req[0]).is_file():
        req = [r.strip() for r in Path(a.req[0]).read_text(encoding="utf-8").split() if r.strip()]
    else:
        req = a.req
    c = curate(req, master, profile=a.profile)
    do = generate_do(c, master)
    Path(a.out).write_text(do, encoding="utf-8")
    readme = Path(a.out).with_name(Path(a.out).stem + "_README.txt")
    readme.write_text(generate_readme(c, master), encoding="utf-8")
    print(f"found={len(c['found'])} missing={c['missing']} wajib+={c['mandatory_added']}")
    print(f"-> {a.out} + {readme}")


def main():
    p = argparse.ArgumentParser(prog="bps-curator")
    sub = p.add_subparsers(dest="cmd", required=True)
    q = sub.add_parser("parse")
    q.add_argument("xlsx")
    q.add_argument("--survey", default="")
    q.add_argument("--period", default="")
    q.add_argument("-o", "--out", required=True)
    q.set_defaults(fn=cmd_parse)
    q = sub.add_parser("curate")
    q.add_argument("--master", required=True)
    q.add_argument("--req", nargs="+", required=True, help="kode variabel atau 1 file berisi daftar")
    q.add_argument("--profile", default=None)
    q.add_argument("-o", "--out", required=True)
    q.set_defaults(fn=cmd_curate)
    a = p.parse_args()
    a.fn(a)


if __name__ == "__main__":
    main()
