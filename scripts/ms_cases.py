#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ms_cases.py: MeterSphere 功能用例操作(列表/详情/创建/编辑/删除)。

生成器输出 JSON 的用例 schema(instance.preconditions/priority/steps[{action,expected}])
由 convert 命令转换为 MS 落库 payload(caseEditType=STEP, steps 为 JSON 字符串,
优先级写入 template 的 functional_priority customField)。

用法:
  python ms_cases.py list [--module <uid>] [--keyword <kw>] [--limit N] [--project <pid>]
  python ms_cases.py get --id <case_id> [--project <pid>]
  python ms_cases.py convert --case <case.json> [--project <pid>] [--module <uid>]
  python ms_cases.py create --case <case.json> [--project <pid>] [--module <uid>] [--dry-run]
  python ms_cases.py edit --id <case_id> --case <case.json> [--project <pid>] [--dry-run]
  python ms_cases.py delete --id <case_id> [--project <pid>] [--dry-run] [--yes]

⚠️ 删除为高风险操作(软删进回收站),必须 --yes 且建议只在沙箱用例上执行。
"""
import argparse
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ms_client  # noqa: E402
from ms_session import load_session, save_session  # noqa: E402

FALLBACK_VERSION_ID = "886962286239814"  # 本项目从既有用例观测到的默认版本


def default_project(session):
    return session.get("project_id") or ms_client.PROJECT_ID


def resolve_template(session, project_id):
    """获取默认模板及 functional_priority 自定义字段 id,缓存到 session。"""
    cached = session.get("template")
    if cached and cached.get("template_id"):
        return cached, None
    resp = ms_client.request_json("GET", "/functional/case/default/template/field/{}".format(project_id))
    if not ms_client.is_ok(resp):
        return None, "获取模板失败: {}".format(ms_client.err_msg(resp))
    data = resp.get("data") or {}
    template_id = data.get("id") or ""
    priority_field_id = ""
    for f in data.get("customFields") or []:
        if f.get("internalFieldKey") == "functional_priority":
            priority_field_id = f.get("fieldId") or ""
    info = {"template_id": template_id, "priority_field_id": priority_field_id}
    session.setdefault("template", {}).update(info)
    session["template_id"] = template_id
    save_session(session)
    return info, None


def resolve_version(session, project_id):
    """版本解析顺序: 环境变量 → 版本接口 → 既有用例抽样 → 观测默认值。"""
    env_v = os.environ.get("METERSPHERE_DEFAULT_VERSION_ID", "").strip()
    if env_v:
        return env_v, "env"
    if session.get("version_id"):
        return session["version_id"], "session"
    candidates = [
        ("GET", "/project/version/{}".format(project_id), None),
        ("GET", "/functional/case/version/{}".format(project_id), None),
    ]
    for method, path, body in candidates:
        resp = ms_client.request_json(method, path, body)
        if ms_client.is_ok(resp):
            data = resp.get("data")
            if isinstance(data, list) and data:
                vid = data[0].get("id") or ""
                if vid:
                    session["version_id"] = vid
                    save_session(session)
                    return vid, path
    resp = ms_client.request_json("POST", "/functional/case/page",
                                  {"projectId": project_id, "current": 1, "pageSize": 1})
    if ms_client.is_ok(resp):
        lst = (resp.get("data") or {}).get("list") or []
        if lst and lst[0].get("versionId"):
            session["version_id"] = lst[0]["versionId"]
            save_session(session)
            return session["version_id"], "case-sample"
    return FALLBACK_VERSION_ID, "fallback"


def list_cases(project_id, module_id=None, keyword=None, limit=100):
    body = {"projectId": project_id}
    if module_id:
        body["moduleIds"] = [module_id]
    if keyword:
        body["keyword"] = keyword
    result = ms_client.page_all("/functional/case/page", body, page_size=min(limit, 100))
    if result["status"] != "success":
        return result
    return {"status": "success", "cases": result["list"][:limit], "total": result["total"]}


def get_case(project_id, case_id):
    resp = ms_client.request_json("GET", "/functional/case/detail/{}".format(case_id))
    if not ms_client.is_ok(resp):
        return {"status": "error", "msg": ms_client.err_msg(resp)}
    return {"status": "success", "case": resp.get("data")}


def convert_case(node, project_id, module_id, template_id, priority_field_id, version_id):
    """把 LLM 生成器输出的用例节点转成 MS 落库 payload。"""
    name = (node.get("name") or "").strip()
    if not name:
        return None, "用例缺少 name"
    instance = node.get("instance") or {}
    raw_steps = instance.get("steps") or []
    steps = []
    for i, step in enumerate(raw_steps, start=1):
        if isinstance(step, dict):
            steps.append({"num": i, "desc": step.get("action") or "", "result": step.get("expected") or ""})
    if not steps:
        steps = [{"num": 1, "desc": name, "result": "结果符合预期"}]
    priority = instance.get("priority") or "P1"
    if priority not in ("P0", "P1", "P2", "P3"):
        priority = "P1"
    custom_fields = []
    if priority_field_id:
        custom_fields.append({"fieldId": priority_field_id, "value": priority})
    payload = {
        "projectId": project_id,
        "moduleId": module_id,
        "templateId": template_id,
        "versionId": version_id,
        "name": name[:255],
        "caseEditType": "STEP",
        "steps": json.dumps(steps, ensure_ascii=False),
        "prerequisite": instance.get("preconditions") or "",
        "remark": node.get("description") or "",
        "aiCreate": True,
        "customFields": custom_fields,
        "tags": node.get("tags") or [],
    }
    return payload, None


def cmd_list(args, session):
    pid = args.project or default_project(session)
    return list_cases(pid, args.module, args.keyword, args.limit or 100)


def cmd_get(args, session):
    pid = args.project or default_project(session)
    if not args.id:
        return {"status": "error", "msg": "--id 必填"}
    return get_case(pid, args.id)


def build_payload(args, session, pid):
    if not args.case:
        return None, "--case 必填(生成器输出的用例 JSON 文件或 JSON 文本)"
    raw = args.case
    if os.path.exists(raw):
        with open(raw, "r", encoding="utf-8-sig") as f:
            data = json.load(f)
    else:
        data = json.loads(raw)
    if isinstance(data, list):
        if len(data) != 1:
            return None, "一次只处理一个用例;列表须为单元素"
        node = data[0]
    else:
        node = data
    if not args.module:
        return None, "--module 必填(目标模块 uid)"
    template, err = resolve_template(session, pid)
    if err:
        return None, err
    version_id, _ = resolve_version(session, pid)
    payload, err = convert_case(node, pid, args.module, template["template_id"],
                                template["priority_field_id"], version_id)
    return payload, err


def cmd_convert(args, session):
    """把生成器用例 JSON 转换为 MS 落库 payload(不写入服务器)。"""
    pid = args.project or default_project(session)
    payload, err = build_payload(args, session, pid)
    if err:
        return {"status": "error", "msg": err}
    return {"status": "success", "dry_run": True, "payload": payload,
            "msg": "[convert] 已生成落库 payload(未写入)"}


def cmd_create(args, session):
    pid = args.project or default_project(session)
    payload, err = build_payload(args, session, pid)
    if err:
        return {"status": "error", "msg": err}
    if args.dry_run:
        return {"status": "success", "dry_run": True, "payload": payload,
                "msg": "[dry-run] 将创建用例: {}".format(payload.get("name"))}
    resp = ms_client.request_multipart("POST", "/functional/case/add", obj=payload)
    if not ms_client.is_ok(resp):
        return {"status": "error", "msg": "创建用例失败: {}".format(ms_client.err_msg(resp))}
    return {"status": "success", "case": resp.get("data"), "msg": "用例创建成功"}


def cmd_edit(args, session):
    pid = args.project or default_project(session)
    if not args.id:
        return {"status": "error", "msg": "--id 必填"}
    payload, err = build_payload(args, session, pid)
    if err:
        return {"status": "error", "msg": err}
    payload["id"] = args.id
    if args.dry_run:
        return {"status": "success", "dry_run": True, "payload": payload,
                "msg": "[dry-run] 将编辑用例: {}".format(payload.get("name"))}
    resp = ms_client.request_multipart("POST", "/functional/case/edit", obj=payload)
    if not ms_client.is_ok(resp):
        return {"status": "error", "msg": "编辑用例失败: {}".format(ms_client.err_msg(resp))}
    return {"status": "success", "case": resp.get("data"), "msg": "用例编辑成功"}


def cmd_delete(args, session):
    pid = args.project or default_project(session)
    if args.dry_run:
        return {"status": "success", "dry_run": True,
                "msg": "[dry-run] 将删除用例(id={}, 软删进回收站)".format(args.id)}
    if not args.yes:
        return {"status": "error", "msg": "删除用例为高风险操作,必须显式加 --yes 确认"}
    resp = ms_client.request_json("POST", "/functional/case/delete",
                                  {"id": args.id, "projectId": pid, "deleteAll": True})
    if not ms_client.is_ok(resp):
        resp2 = ms_client.request_json("POST", "/functional/case/batch/delete-to-gc",
                                       {"projectId": pid, "selectIds": [args.id],
                                        "selectAll": False, "deleteAll": True})
        if not ms_client.is_ok(resp2):
            return {"status": "error",
                    "msg": "删除失败,POST /delete 与 POST /batch/delete-to-gc 均未成功: 最后错误: {}".format(ms_client.err_msg(resp2))}
        return {"status": "success", "id": args.id, "msg": "用例已删除(batch/delete-to-gc)"}
    return {"status": "success", "id": args.id, "msg": "用例已删除"}


def main():
    parser = argparse.ArgumentParser(add_help=False)
    sub = parser.add_subparsers(dest="cmd")
    for name in ("list", "get", "convert", "create", "edit", "delete"):
        p = sub.add_parser(name)
        p.add_argument("--module", default=None)
        p.add_argument("--keyword", default=None)
        p.add_argument("--limit", type=int, default=None)
        p.add_argument("--id", default=None)
        p.add_argument("--case", default=None)
        p.add_argument("--project", default=None)
        p.add_argument("--dry-run", action="store_true")
        p.add_argument("--yes", action="store_true")
    args = parser.parse_args()
    handlers = {"list": cmd_list, "get": cmd_get, "convert": cmd_convert,
                "create": cmd_create, "edit": cmd_edit, "delete": cmd_delete}
    if not args.cmd:
        print(json.dumps({"status": "error",
                          "msg": "用法: ms_cases.py list|get|convert|create|edit|delete ..."}, ensure_ascii=False))
        sys.exit(1)
    session = load_session()
    result = handlers[args.cmd](args, session)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    sys.exit(0 if result.get("status") == "success" else 1)


if __name__ == "__main__":
    main()
