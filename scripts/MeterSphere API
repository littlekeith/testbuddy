#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MeterSphere API 客户端(自包含版)。

三个 testbuddy-ms skill 的 scripts/ 各内置一份本文件副本,修改时保持同步。
鉴权方式与 metersphere skill 一致: accessKey + signature。
签名: plain = {AK}|{uuid}|{timestamp_ms}, 经 openssl AES-128-CBC(SK 为 key, AK 为 iv, base64)。
配置读取: skill 目录下 .env(load_dotenv), 外部环境变量优先。
"""

import json
import os
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
ENV_FILE = SKILL_DIR / ".env"


def load_dotenv(dotenv_path=None):
    if dotenv_path and os.path.exists(dotenv_path):
        for line in Path(dotenv_path).read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                os.environ.setdefault(k, v)


if ENV_FILE.exists():
    load_dotenv(ENV_FILE)

BASE_URL = os.environ.get("METERSPHERE_BASE_URL", "").rstrip("/")
ACCESS_KEY = os.environ.get("METERSPHERE_ACCESS_KEY", "")
SECRET_KEY = os.environ.get("METERSPHERE_SECRET_KEY", "")
PROJECT_ID = os.environ.get("METERSPHERE_PROJECT_ID", "")
ORG_ID = os.environ.get("METERSPHERE_ORGANIZATION_ID", "100001")

OK_CODE = 100200


def die(msg):
    print(json.dumps({"status": "error", "msg": msg}, ensure_ascii=False, indent=2))
    sys.exit(1)


def check_config():
    missing = []
    if not BASE_URL:
        missing.append("METERSPHERE_BASE_URL")
    if not ACCESS_KEY:
        missing.append("METERSPHERE_ACCESS_KEY")
    if not SECRET_KEY:
        missing.append("METERSPHERE_SECRET_KEY")
    if missing:
        die("缺少环境变量: {}。请在 skill 目录放置 .env 或设置外部环境变量".format(", ".join(missing)))


def signature():
    check_config()
    try:
        import base64
        from Crypto.Cipher import AES
        from Crypto.Util.Padding import pad
        plain = "{}|{}|{}".format(ACCESS_KEY, uuid.uuid4(), int(time.time() * 1000)).encode("utf-8")
        cipher = AES.new(SECRET_KEY.encode("utf-8"), AES.MODE_CBC, ACCESS_KEY.encode("utf-8"))
        encrypted = cipher.encrypt(pad(plain, AES.block_size))
        return base64.b64encode(encrypted).decode("utf-8")
    except Exception:
        plain = "{}|{}|{}".format(ACCESS_KEY, uuid.uuid4(), int(time.time() * 1000))
        proc = subprocess.run(
            [
                "openssl", "enc", "-aes-128-cbc",
                "-K", SECRET_KEY.encode("utf-8").hex(),
                "-iv", ACCESS_KEY.encode("utf-8").hex(),
                "-base64", "-A", "-nosalt",
            ],
            input=plain.encode("utf-8"),
            capture_output=True,
            check=True,
        )
        return proc.stdout.decode("utf-8").strip()


def headers():
    check_config()
    return {
        "Content-Type": "application/json",
        "accessKey": ACCESS_KEY,
        "signature": signature(),
    }


def is_ok(resp):
    return isinstance(resp, dict) and resp.get("code") == OK_CODE


def err_msg(resp):
    if isinstance(resp, dict):
        msg = resp.get("message") or resp.get("messageDetail") or ""
        if msg and msg != "null":
            return msg
        return str(resp)[:500]
    return str(resp)[:500]


def request_json(method, path, body=None, timeout=60):
    """发送 JSON 请求,返回解析后的响应 dict。"""
    check_config()
    data = None if body is None else json.dumps(body, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(BASE_URL + path, data=data, headers=headers(), method=method)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return {"code": -1, "message": "HTTP {}: {}".format(e.code, raw[:500])}
    except Exception as e:
        return {"code": -1, "message": str(e)}


def request_multipart(method, path, json_field="request", obj=None, extra_fields=None, timeout=60):
    """发送 multipart/form-data 请求(功能用例 add/edit 需要 request 字段)。"""
    check_config()
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex
    lines = []

    def add_field(name, value, content_type=None):
        lines.append("--" + boundary)
        lines.append('Content-Disposition: form-data; name="{}"'.format(name))
        if content_type:
            lines.append("Content-Type: " + content_type)
        lines.append("")
        lines.append(str(value))

    if json_field and obj is not None:
        add_field(json_field, json.dumps(obj, ensure_ascii=False), content_type="application/json")
    for k, v in (extra_fields or {}).items():
        add_field(k, v, content_type="text/plain; charset=UTF-8")
    lines.append("--" + boundary + "--")
    lines.append("")
    payload = "\r\n".join(lines).encode("utf-8")
    req = urllib.request.Request(
        BASE_URL + path,
        data=payload,
        headers={
            "accessKey": ACCESS_KEY,
            "signature": signature(),
            "Content-Type": "multipart/form-data; boundary=" + boundary,
        },
        method=method,
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8", errors="replace"))
    except urllib.error.HTTPError as e:
        raw = e.read().decode("utf-8", errors="replace")
        return {"code": -1, "message": "HTTP {}: {}".format(e.code, raw[:500])}
    except Exception as e:
        return {"code": -1, "message": str(e)}


def page_all(path, body=None, page_size=100, max_pages=200):
    """分页拉取全部数据。body 需要 projectId 等参数,current/pageSize 自动补充。
    返回 data 的 list 字段。"""
    body = dict(body or {})
    body.setdefault("current", 1)
    body["pageSize"] = page_size
    rows = []
    for page in range(1, max_pages + 1):
        body["current"] = page
        resp = request_json("POST", path, body)
        if not is_ok(resp):
            return {"status": "error", "msg": err_msg(resp)}
        data = resp.get("data") or {}
        lst = data.get("list") or []
        rows.extend(lst)
        total = data.get("total") or len(rows)
        if not lst or len(rows) >= total:
            break
    return {"status": "success", "list": rows, "total": len(rows)}


if __name__ == "__main__":
    print(json.dumps({"status": "ok", "base_url": BASE_URL, "project_id": PROJECT_ID, "org_id": ORG_ID}, ensure_ascii=False))
