#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ms_search.py: 查询模块树/功能用例/设计落库映射。

用法:
  python ms_search.py modules [--flat] [--project <pid>]
  python ms_search.py cases [--module <uid>] [--keyword <kw>] [--limit N] [--project <pid>]
  python ms_search.py mapping [--id <design_id>|--latest]
  python ms_search.py session
"""
import argparse
import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ms_cases  # noqa: E402
import ms_modules  # noqa: E402
from ms_session import find_workspace_root, load_session  # noqa: E402


def mapping_dirs():
    ws = find_workspace_root()
    base = os.path.join(ws, ".testbuddy", "designs")
    return [d for d in glob.glob(os.path.join(base, "*")) if os.path.isdir(d)]


def load_mapping(design_id=None, latest=False):
    dirs = mapping_dirs()
    if not dirs:
        return None, "没有找到任何设计落库映射(.testbuddy/designs/*)"
    if latest:
        target = max(dirs, key=os.path.getmtime)
    else:
        cands = [d for d in dirs if os.path.basename(d) == design_id]
        if not cands:
            return None, "未找到 design_id={} 的映射,可用: {}".format(
                design_id, [os.path.basename(d) for d in dirs])
        target = cands[0]
    path = os.path.join(target, "design_mapping.json")
    if not os.path.exists(path):
        return None, "映射文件缺失: {}".format(path)
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f), None


def cmd_modules(args):
    session = load_session()
    pid = args.project or session.get("project_id") or ms_modules.ms_client.PROJECT_ID
    result = ms_modules.cmd_list(args, session)
    if result["status"] == "success":
        result["project"] = pid
    return result


def cmd_cases(args):
    session = load_session()
    pid = args.project or session.get("project_id") or ms_cases.ms_client.PROJECT_ID
    return ms_cases.list_cases(pid, args.module, args.keyword, args.limit or 100)


def cmd_mapping(args):
    data, err = load_mapping(args.id, args.latest)
    if err:
        return {"status": "error", "msg": err}
    return {"status": "success", "mapping": data}


def cmd_session(args):
    return {"status": "success", "session": load_session()}


def main():
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="cmd")
    for name in ("modules", "cases", "mapping", "session"):
        p = sub.add_parser(name)
        p.add_argument("--flat", action="store_true")
        p.add_argument("--project", default=None)
        p.add_argument("--module", default=None)
        p.add_argument("--keyword", default=None)
        p.add_argument("--limit", type=int, default=None)
        p.add_argument("--id", default=None)
        p.add_argument("--latest", action="store_true")
    args = parser.parse_args()
    handlers = {"modules": cmd_modules, "cases": cmd_cases, "mapping": cmd_mapping, "session": cmd_session}
    if not args.cmd:
        print(json.dumps({"status": "error", "msg": "用法: ms_search.py modules|cases|mapping|session ..."}, ensure_ascii=False))
        sys.exit(1)
    result = handlers[args.cmd](args)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
