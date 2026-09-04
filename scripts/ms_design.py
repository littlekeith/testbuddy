#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ms_design.py: 测试设计落地编排器。

把生成器输出的设计 JSON(节点树: FEATURE→SCENE→TEST_POINT/CASE)落库到 MeterSphere:

- FEATURE   → 一级模块(挂在根模块下)
- SCENE     → 二级模块(挂在所属 FEATURE 模块下)
- TEST_POINT→ 不建模块,作为其下用例的名称前缀 "{测试点名}::"
- CASE      → 功能用例(写入最近 SCENE/FEATURE/根模块),tags=[FEATURE名, SCENE名]

用法:
  python ms_design.py --design <design.json> [--name <设计名>] [--parent <模块uid|root>]
                      [--project <pid>] [--dry-run]
白名单文件: 生成器(.testbuddy/designs 或工作区内)输出的 JSON。
"""
import argparse
import json
import os
import re
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ms_client  # noqa: E402
import ms_cases  # noqa: E402
import ms_modules  # noqa: E402
from ms_session import find_workspace_root, load_session, save_session  # noqa: E402


def load_design_file(path):
    ext = os.path.splitext(path)[1].lower()
    with open(path, "r", encoding="utf-8-sig") as f:
        content = f.read()
    if ext == ".json":
        return json.loads(content)
    m = re.search(r"```json\s*\n(.*?)\n```", content, re.DOTALL)
    if m:
        return json.loads(m.group(1))
    m = re.search(r"```yaml\s*\n(.*?)\n```", content, re.DOTALL)
    if m:
        try:
            import yaml
            return yaml.safe_load(m.group(1))
        except Exception:
            pass
    return json.loads(content)


def flatten_tree_nodes(data, parent_uid=None, out=None):
    if out is None:
        out = []
    if isinstance(data, dict):
        data = [data]
    for node in data or []:
        if not isinstance(node, dict) or "kind" not in node:
            continue
        item = {k: v for k, v in node.items() if k != "children"}
        if parent_uid is not None and not item.get("parent_uid"):
            item["parent_uid"] = parent_uid
        out.append(item)
        children = node.get("children") or []
        for child in children:
            flatten_tree_nodes(child, item.get("uid"), out)
    return out


def classify(nodes):
    by_uid = {n.get("uid"): n for n in nodes if n.get("uid")}
    children = {}
    for n in nodes:
        children.setdefault(n.get("parent_uid"), []).append(n)
    return by_uid, children


def resolve_module(args, session, name, parent_uid, pid, created_plan):
    """find-or-create 模块,返回 (module_uid, created)。"""
    tree = ms_modules.tree(pid)
    if tree["status"] != "success":
        raise RuntimeError(tree["msg"])
    found = ms_modules.find_by_name(tree["tree"], name, parent_uid)
    if found:
        return found[0].get("id"), False
    if args.dry_run:
        created_plan.append({"name": name, "parent": parent_uid, "creation": "dry-run"})
        return "<dry-run-{}>".format(name), True
    parent_api = ms_modules.normalize_parent(parent_uid)
    resp = ms_client.request_json("POST", "/functional/case/module/add",
                                  {"projectId": pid, "parentId": parent_api, "name": name})
    if not ms_client.is_ok(resp):
        raise RuntimeError("创建模块失败 {}: {}".format(name, ms_client.err_msg(resp)))
    tree2 = ms_modules.tree(pid)
    found2 = ms_modules.find_by_name(tree2["tree"], name, parent_uid) if tree2["status"] == "success" else []
    if found2:
        return found2[0].get("id"), True
    return resp.get("data", {}).get("id") or "<unknown>", True


def run(args):
    session = load_session()
    pid = args.project or session.get("project_id") or ms_client.PROJECT_ID
    if not pid:
        return {"status": "error", "msg": "缺少项目 ID,请在会话或 METERSPHERE_PROJECT_ID 中配置"}
    data = load_design_file(args.design)
    nodes = flatten_tree_nodes(data)
    if not nodes:
        return {"status": "error", "msg": "设计文件中没有有效节点"}
    by_uid, children = classify(nodes)
    root_uids = [n for n in nodes if not n.get("parent_uid") or n.get("parent_uid") not in by_uid]

    design_name = args.name or (session.get("requirement") or {}).get("name") or "未命名设计"
    stamp = time.strftime("%Y%m%d")
    root_module_name = "{}_{}".format(design_name, stamp)

    parent_mount = args.parent or "root"
    created_plan = []
    # 1) 根模块
    root_uid, _ = resolve_module(args, session, root_module_name, parent_mount, pid, created_plan)

    mapping = {"project_id": pid, "design_id": "", "design_name": design_name,
               "root_module_uid": root_uid, "root_module_name": root_module_name,
               "modules": {}, "cases": {}, "created_at": time.strftime("%Y-%m-%d %H:%M:%S")}

    def module_for_feature(feat):
        fname = feat.get("name") or "未命名模块"
        uid, _ = resolve_module(args, session, fname, root_uid, pid, created_plan)
        mapping["modules"][feat.get("uid")] = {"module_uid": uid, "module_name": fname, "kind": "FEATURE", "parent": root_uid}
        return uid

    def module_for_scene(scene, feat_uid):
        sname = scene.get("name") or "未命名场景"
        parent = mapping["modules"].get(feat_uid, {}).get("module_uid") or root_uid
        uid, _ = resolve_module(args, session, sname, parent, pid, created_plan)
        mapping["modules"][scene.get("uid")] = {"module_uid": uid, "module_name": sname, "kind": "SCENE", "parent": parent}
        return uid

    def parent_module_for_case(node):
        """沿祖先链找最近的 SCENE/FEATURE 模块 uid。"""
        cur = node.get("parent_uid")
        seen = 0
        while cur and cur in by_uid and seen < 10:
            anc = by_uid[cur]
            if anc.get("kind") == "SCENE" and cur in mapping["modules"]:
                return mapping["modules"][cur]["module_uid"]
            if anc.get("kind") == "FEATURE" and cur in mapping["modules"]:
                return mapping["modules"][cur]["module_uid"]
            cur = anc.get("parent_uid")
            seen += 1
        return root_uid

    def testpoint_prefix(node):
        cur = node.get("parent_uid")
        seen = 0
        while cur and cur in by_uid and seen < 10:
            anc = by_uid[cur]
            if anc.get("kind") == "TEST_POINT":
                return (anc.get("name") or "").strip()
            cur = anc.get("parent_uid")
            seen += 1
        return ""

    template, terr = ms_cases.resolve_template(session, pid)
    if terr:
        return {"status": "error", "msg": terr}
    version_id, _ = ms_cases.resolve_version(session, pid)

    # 2) 依层级创建模块
    for n in nodes:
        kind = (n.get("kind") or "").upper()
        if kind == "FEATURE" and n.get("uid") in by_uid:
            module_for_feature(n)
    for n in nodes:
        kind = (n.get("kind") or "").upper()
        if kind == "SCENE":
            module_for_scene(n, n.get("parent_uid"))

    # 3) 创建用例
    case_results = []
    for n in nodes:
        kind = (n.get("kind") or "").upper()
        if kind != "CASE":
            continue
        module_uid = parent_module_for_case(n)
        prefix = testpoint_prefix(n)
        inst = n.get("instance") or {}
        name = (n.get("name") or "").strip()
        if not name:
            continue
        display_name = "{}::{}".format(prefix, name) if prefix else name
        tags = []
        cur = n.get("parent_uid")
        seen = 0
        while cur and cur in by_uid and seen < 10:
            anc = by_uid[cur]
            if anc.get("kind") in ("FEATURE", "SCENE") and (anc.get("name") or "") not in tags:
                tags.append(anc.get("name"))
            cur = anc.get("parent_uid")
            seen += 1
        case_node = dict(n)
        case_node["name"] = display_name
        case_node["tags"] = tags
        payload, err = ms_cases.convert_case(case_node, pid, module_uid, template["template_id"],
                                             template["priority_field_id"], version_id)
        if err:
            case_results.append({"name": display_name, "status": "error", "msg": err})
            continue
        if args.dry_run:
            case_results.append({"name": display_name, "module_uid": module_uid,
                                 "priority": inst.get("priority") or "P1",
                                 "steps": len(inst.get("steps") or []), "tags": tags,
                                 "status": "dry-run"})
            continue
        resp = ms_client.request_multipart("POST", "/functional/case/add", obj=payload)
        if not ms_client.is_ok(resp):
            case_results.append({"name": display_name, "status": "error",
                                 "msg": ms_client.err_msg(resp)})
            continue
        case_id = (resp.get("data") or {}).get("id") or ""
        if not case_id:
            case_id = lookup_case_id(pid, module_uid, display_name)
        mapping["cases"][n.get("uid")] = {"case_id": case_id, "case_name": display_name,
                                          "module_uid": module_uid, "module_name": mapping["modules"].get(
                                              next((k for k, v in mapping["modules"].items() if v.get("module_uid") == module_uid), ""), {}).get("module_name", "")}
        case_results.append({"name": display_name, "case_id": case_id, "status": "success"})

    summary = {
        "status": "success",
        "dry_run": bool(args.dry_run),
        "project_id": pid,
        "design_name": design_name,
        "root_module_uid": root_uid,
        "root_module_name": root_module_name,
        "modules_planned_created": created_plan,
        "cases": case_results,
        "url": ms_client.BASE_URL,
    }

    if not args.dry_run:
        ws = find_workspace_root()
        design_id = "{}-{}".format(re.sub(r"[^\w\-]+", "_", root_module_name), time.strftime("%H%M%S"))
        mapping["design_id"] = design_id
        mapping_dir = os.path.join(ws, ".testbuddy", "designs", design_id)
        os.makedirs(mapping_dir, exist_ok=True)
        with open(os.path.join(mapping_dir, "design_mapping.json"), "w", encoding="utf-8") as f:
            json.dump(mapping, f, ensure_ascii=False, indent=2)
        session["root_module_uid"] = root_uid
        save_session(session)
        summary["design_id"] = design_id
        summary["mapping_file"] = os.path.join(mapping_dir, "design_mapping.json")
        summary["msg"] = "落地完成,请打开 {} 查看模块树 {}".format(ms_client.BASE_URL, root_module_name)
    else:
        summary["msg"] = "[dry-run] 未发生任何写入"
    return summary


def lookup_case_id(project_id, module_uid, name):
    try:
        result = ms_cases.list_cases(project_id, module_id=module_uid, keyword=name, limit=20)
        if result["status"] == "success":
            for c in result["cases"]:
                if c.get("name") == name:
                    return c.get("id") or ""
    except Exception:
        pass
    return ""


def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--design", required=True)
    parser.add_argument("--name", default=None)
    parser.add_argument("--parent", default=None)
    parser.add_argument("--project", default=None)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    try:
        result = run(args)
    except Exception as e:
        result = {"status": "error", "msg": "执行异常: {}".format(e)}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
