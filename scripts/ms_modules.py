#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ms_modules.py: MeterSphere 功能用例模块树操作。

用法:
  python ms_modules.py list [--project <pid>] [--flat]
  python ms_modules.py create --name <模块名> [--parent <模块uid|root>] [--project <pid>] [--dry-run]
  python ms_modules.py update --id <模块uid> --name <新名称> [--project <pid>] [--dry-run]
  python ms_modules.py delete --id <模块uid> [--project <pid>] [--dry-run] [--yes]

⚠️ 删除接口为 GET /functional/case/module/delete/{id},会级联删除子模块与用例且不进回收站
(参见根目录 INCIDENT-notes.md)。delete 必须 --yes 且建议仅在沙箱模块上使用。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ms_client  # noqa: E402
from ms_session import load_session  # noqa: E402


def default_project(session):
    return session.get("project_id") or ms_client.PROJECT_ID


def normalize_parent(parent):
    """顶层模块在 API 中的父级为 NONE(虚拟根 id 才是 root), 统一归一化。"""
    if parent in (None, "", "root", "NONE"):
        return "NONE"
    return parent



def flatten(nodes, parent_id="NONE", out=None, path="/"):
    if out is None:
        out = []
    for n in nodes:
        node = {
            "id": n.get("id"),
            "name": n.get("name"),
            "type": n.get("type"),
            "parent_id": n.get("parentId") or parent_id,
            "path": n.get("path") or path,
            "count": n.get("count", 0),
        }
        out.append(node)
        flatten(n.get("children") or [], node["id"], out, node["path"])
    return out


def tree(project_id):
    resp = ms_client.request_json("GET", "/functional/case/module/tree/{}".format(project_id))
    if not ms_client.is_ok(resp):
        return {"status": "error", "msg": ms_client.err_msg(resp)}
    return {"status": "success", "tree": resp.get("data") or []}


def cmd_list(args, session):
    pid = args.project or default_project(session)
    result = tree(pid)
    if result["status"] != "success":
        return result
    nodes = flatten(result["tree"])
    if args.flat:
        return {"status": "success", "project": pid, "modules": nodes}
    return {"status": "success", "project": pid, "tree": result["tree"]}


def find_by_name(nodes, name, parent_id, out=None):
    if out is None:
        out = []
    parent_id = normalize_parent(parent_id)
    for n in nodes:
        if n.get("name") == name and (n.get("parentId") or "NONE") == parent_id:
            out.append(n)
        find_by_name(n.get("children") or [], name, parent_id, out)
    return out


def cmd_create(args, session):
    pid = args.project or default_project(session)
    name = (args.name or "").strip()
    parent = normalize_parent(args.parent)
    if not name:
        return {"status": "error", "msg": "--name 必填"}
    data = tree(pid)
    if data["status"] != "success":
        return data
    t = data["tree"]
    existed = find_by_name(t, name, parent)
    if existed:
        return {"status": "success", "created": False, "module": existed[0],
                "msg": "模块已存在: {} (id={})".format(name, existed[0].get("id"))}
    if args.dry_run:
        return {"status": "success", "created": False, "dry_run": True,
                "msg": "[dry-run] 将创建模块: name={}, parentId={}, projectId={}".format(name, parent, pid)}
    resp = ms_client.request_json(
        "POST", "/functional/case/module/add",
        {"projectId": pid, "parentId": parent, "name": name},
    )
    if not ms_client.is_ok(resp):
        return {"status": "error", "msg": "创建模块失败: {}".format(ms_client.err_msg(resp))}
    # 回查确认
    data2 = tree(pid)
    if data2["status"] == "success":
        found = find_by_name(data2["tree"], name, parent)
        if found:
            return {"status": "success", "created": True, "module": found[0],
                    "msg": "模块创建成功: {} (id={})".format(name, found[0].get("id"))}
    return {"status": "success", "created": True, "module": resp.get("data"),
            "msg": "模块创建请求已发送(未回查到,请人工确认)"}


def cmd_update(args, session):
    pid = args.project or default_project(session)
    if not args.id or not args.name:
        return {"status": "error", "msg": "--id 与 --name 必填"}
    if args.dry_run:
        return {"status": "success", "dry_run": True,
                "msg": "[dry-run] 将重命名模块: id={}, newName={}".format(args.id, args.name)}
    resp = ms_client.request_json(
        "POST", "/functional/case/module/update",
        {"id": args.id, "projectId": pid, "name": args.name},
    )
    if not ms_client.is_ok(resp):
        return {"status": "error", "msg": "重命名模块失败: {}".format(ms_client.err_msg(resp))}
    return {"status": "success", "id": args.id, "name": args.name}


def cmd_delete(args, session):
    pid = args.project or default_project(session)
    if args.dry_run:
        return {"status": "success", "dry_run": True,
                "msg": "[dry-run] 将删除模块(级联删除子模块与用例): id={}, projectId={}".format(args.id, pid)}
    if not args.yes:
        return {"status": "error",
                "msg": "模块删除会级联删除子模块与用例且不进回收站,必须显式加 --yes 确认"}
    resp = ms_client.request_json("GET", "/functional/case/module/delete/{}".format(args.id))
    if not ms_client.is_ok(resp):
        return {"status": "error", "msg": "删除模块失败: {}".format(ms_client.err_msg(resp))}
    return {"status": "success", "id": args.id, "msg": "模块已删除(级联)"}


def main():
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="cmd")
    for name in ("list", "create", "update", "delete"):
        p = sub.add_parser(name)
        p.add_argument("--project", default=None)
        p.add_argument("--name", default=None)
        p.add_argument("--parent", default=None)
        p.add_argument("--id", default=None)
        p.add_argument("--flat", action="store_true")
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    if not args.cmd:
        print(json.dumps({"status": "error", "msg": "用法: ms_modules.py list|create|update|delete ..."}, ensure_ascii=False))
        sys.exit(1)
    session = load_session()
    if args.cmd == "list":
        result = cmd_list(args, session)
    elif args.cmd == "create":
        result = cmd_create(args, session)
    elif args.cmd == "update":
        result = cmd_update(args, session)
    else:
        result = cmd_delete(args, session)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
