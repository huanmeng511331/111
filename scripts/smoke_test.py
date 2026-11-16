#!/usr/bin/env python3
"""HSE 隐患闭环 API 冒烟测试（仅依赖 Python 标准库）。

使用前请先启动后端，例如：
    cd backend && uvicorn app.main:app --port 8000

运行：
    python3 scripts/smoke_test.py
    python3 scripts/smoke_test.py --base-url http://localhost:8010
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.error
import urllib.request
from datetime import date, timedelta


class SmokeFailure(Exception):
    """冒烟测试断言失败。"""


class ApiClient:
    def __init__(self, base_url: str) -> None:
        self.api = base_url.rstrip("/") + "/api"

    def call(
        self,
        method: str,
        path: str,
        payload: dict | None = None,
        expect: int = 200,
    ) -> dict:
        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        request = urllib.request.Request(
            self.api + path,
            data=data,
            method=method,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=15) as response:
                body = response.read()
                status = response.status
        except urllib.error.HTTPError as exc:
            body = exc.read()
            status = exc.code
        except urllib.error.URLError as exc:
            raise SmokeFailure(
                f"无法连接 {self.api}，请确认后端已启动（{exc.reason}）"
            ) from exc

        try:
            parsed = json.loads(body or b"null")
        except json.JSONDecodeError as exc:
            raise SmokeFailure(f"{method} {path} 返回非 JSON：{body[:200]!r}") from exc

        if status != expect:
            raise SmokeFailure(f"{method} {path} 期望 {expect}，实际 {status}：{parsed}")
        return parsed


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SmokeFailure(message)


def run(base_url: str) -> None:
    client = ApiClient(base_url)
    due_date = (date.today() + timedelta(days=5)).isoformat()

    health = client.call("GET", "/health")
    require(health.get("status") == "ok", f"健康检查异常：{health}")
    print("[1/12] 健康检查通过")

    listing = client.call("GET", "/hazards?page_size=5")
    require(isinstance(listing.get("items"), list), "列表响应缺少 items")
    require(listing.get("total", 0) >= 1, "列表为空，演示数据未初始化")
    print(f"[2/12] 列表查询通过，共 {listing['total']} 条")

    options = client.call("GET", "/hazards/options")
    require(bool(options.get("types")) and bool(options.get("levels")), "枚举选项为空")
    print("[3/12] 枚举选项通过")

    created = client.call(
        "POST",
        "/hazards",
        {
            "hazard_type": "消防安全",
            "hazard_level": "一般",
            "location": "1号厂房东侧消防通道",
            "description": "消防通道堆放杂物，影响应急疏散。",
            "reporter": "张伟",
            "due_date": due_date,
        },
        expect=201,
    )
    hazard_id = created["id"]
    require(created["status"] == "待审核", "上报后状态应为待审核")
    require(created["owner"] is None, "待审核隐患不应有责任人")
    require(created["hazard_no"].startswith("HSE-"), "隐患编号格式不正确")
    print(f"[4/12] 上报隐患通过：{created['hazard_no']}")

    assigned = client.call(
        "PATCH",
        f"/hazards/{hazard_id}/assign",
        {"owner": "李强", "due_date": due_date, "comment": "请三日内完成清理"},
    )
    require(assigned["status"] == "整改中", "分派后状态应为整改中")
    require(assigned["owner"] == "李强", "责任人未保存")
    print("[5/12] 审核分派通过")

    rectified = client.call(
        "PATCH",
        f"/hazards/{hazard_id}/rectification",
        {
            "rectification_measure": "清理通道杂物并设置禁放标识",
            "rectification_result": "已清理并设置禁放标识",
            "operator": "李强",
        },
    )
    require(rectified["status"] == "待验收", "提交整改后状态应为待验收")
    print("[6/12] 提交整改通过")

    closed = client.call(
        "PATCH",
        f"/hazards/{hazard_id}/acceptance",
        {"approved": True, "acceptance_comment": "现场复核已整改到位，同意关闭"},
    )
    require(closed["status"] == "已关闭", "验收通过后状态应为已关闭")
    actions = [log["action"] for log in closed["logs"]]
    require(
        actions == ["create", "assign", "submit_rectification", "accept"],
        f"流转记录不完整：{actions}",
    )
    print("[7/12] 验收关闭通过，流转记录完整")

    client.call(
        "PATCH",
        f"/hazards/{hazard_id}/acceptance",
        {"approved": True, "acceptance_comment": "重复验收"},
        expect=409,
    )
    print("[8/12] 非法流转返回 409 通过")

    detail = client.call("GET", f"/hazards/{hazard_id}")
    require(detail["status"] == "已关闭", "详情状态与关闭结果不一致")
    print("[9/12] 详情查询通过")

    client.call("GET", "/hazards/999999", expect=404)
    print("[10/12] 不存在记录返回 404 通过")

    client.call(
        "POST",
        "/hazards",
        {
            "hazard_type": "未知类型",
            "hazard_level": "一般",
            "location": "x",
            "description": "太短",
            "reporter": "张",
            "due_date": "2000-01-01",
        },
        expect=422,
    )
    print("[11/12] 参数校验返回 422 通过")

    statistics = client.call("GET", "/hazards/statistics")
    require(
        {"待审核", "整改中", "待验收", "已关闭"} <= set(statistics["status_counts"]),
        "统计数据缺少状态维度",
    )
    require(statistics["status_counts"]["已关闭"] >= 1, "已关闭数量应至少为 1")
    require(len(statistics["recent_7_days"]) == 7, "趋势数据应为 7 天")
    print(
        "[12/12] 统计查询通过："
        f"{statistics['status_counts']}，超期 {statistics['overdue_count']} 条"
    )

    print("\n冒烟测试全部通过（本次新增一条演示隐患并已关闭，可作为演示数据保留）。")


def main() -> int:
    parser = argparse.ArgumentParser(description="HSE 隐患闭环 API 冒烟测试")
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="后端地址，默认 http://localhost:8000",
    )
    args = parser.parse_args()

    try:
        run(args.base_url)
    except SmokeFailure as exc:
        print(f"\n冒烟测试失败：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
