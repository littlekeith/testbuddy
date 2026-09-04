#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ms_session.py: 读取/回写设计会话(.testbuddy/env/session.json)。

会话字段: project_id / org_id / root_module_uid / template_id / version_id /
requirement(requirement_text/name/source/file) / env / mode(chat)
"""
import json
import os
import sys

DEFAULT_MODE = "chat"


def find_workspace_root():
    """从当前目录向上查找包含 .testbuddy 的工作区根目录,找不到则回退 cwd。"""
    cwd = os.getcwd()
    current = cwd
    while True:
        if os.path.isdir(os.path.join(current, ".testbuddy")):
            return current
        parent = os.path.dirname(current)
        if parent == current:
            return cwd
        current = parent


def session_file():
    return os.path.join(find_workspace_root(), ".testbuddy", "env", "session.json")


def detect_env():
    if os.environ.get("CODEBUDDY_COPILOT_INTERNET_ENVIRONMENT"):
        return "codebuddy"
    if os.environ.get("CODEX_CI") or os.environ.get("CODEX_HOME"):
        return "codex"
    return "other"


def default_session():
    return {
        "mode": DEFAULT_MODE,
        "env": detect_env(),
        "project_id": os.environ.get("METERSPHERE_PROJECT_ID", ""),
        "org_id": os.environ.get("METERSPHERE_ORGANIZATION_ID", "100001"),
        "root_module_uid": "",
        "template_id": "",
        "version_id": "",
        "requirement": {},
    }


def load_session():
    path = session_file()
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                if isinstance(data, dict):
                    base = default_session()
                    for k, v in data.items():
                        base[k] = v
                    return base
            except Exception:
                pass
    return default_session()


def save_session(data):
    path = session_file()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def merge_session(existing, new_data):
    """合并: dict 字段 key 级合并,其他直接覆盖。"""
    for key, value in new_data.items():
        if isinstance(value, dict):
            existing.setdefault(key, {})
            if not isinstance(existing[key], dict):
                existing[key] = {}
            existing[key].update(value)
        else:
            existing[key] = value
    return existing


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "--write":
        raw = sys.stdin.read().strip()
        try:
            new_data = json.loads(raw)
        except Exception as e:
            print(json.dumps({"status": "error", "msg": "stdin 不是合法 JSON: {}".format(e)}, ensure_ascii=False))
            sys.exit(1)
        existing = load_session()
        merged = merge_session(existing, new_data)
        save_session(merged)
        print(json.dumps({"status": "success", "session": merged}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"status": "success", "session": load_session()}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
