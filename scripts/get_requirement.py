#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""get_requirement.py: 获取/保存需求来源(仅允许用户粘贴文本或本地文件)。

用法:
  python get_requirement.py --text "<需求文本>"
  python get_requirement.py --file <prd.md> [--name <需求名>]
不传参数时仅展示当前会话需求。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ms_session import load_session, save_session  # noqa: E402


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--text", default=None)
    parser.add_argument("--file", default=None)
    parser.add_argument("--name", default=None)
    args, _ = parser.parse_known_args()

    session = load_session()

    if args.file and args.text:
        print(json.dumps({"status": "error", "msg": "--text 与 --file 只能二选一"}, ensure_ascii=False))
        sys.exit(1)

    if args.file:
        if not os.path.exists(args.file):
            print(json.dumps({"status": "error", "msg": "需求文件不存在: {}".format(args.file)}, ensure_ascii=False))
            sys.exit(1)
        with open(args.file, "r", encoding="utf-8-sig") as f:
            text = f.read()
        name = args.name or os.path.splitext(os.path.basename(args.file))[0]
        req = {"text": text, "name": name, "source": "file", "file": os.path.abspath(args.file)}
    elif args.text:
        text = args.text.strip()
        if not text:
            print(json.dumps({"status": "error", "msg": "需求文本为空"}, ensure_ascii=False))
            sys.exit(1)
        first_line = text.splitlines()[0].strip() if text.splitlines() else ""
        name = args.name or first_line[:40] or "未命名需求"
        req = {"text": text, "name": name, "source": "text", "file": ""}
    else:
        req = session.get("requirement") or {}
        print(json.dumps({"status": "success", "requirement": req}, ensure_ascii=False, indent=2))
        return

    session["requirement"] = req
    save_session(session)
    print(json.dumps({"status": "success", "requirement": req}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
