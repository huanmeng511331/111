"""隐患 API 业务闭环测试。"""

from __future__ import annotations

from datetime import date, timedelta

import pytest
from fastapi.testclient import TestClient

from app.main import create_app


@pytest.fixture()
def client(tmp_path):
    app = create_app(tmp_path / "test.db")
    with TestClient(app) as test_client:
        yield test_client


def _payload(**overrides):
    data = {
        "hazard_type": "消防安全",
        "hazard_level": "一般",
        "location": "1号厂房东侧消防通道",
        "description": "消防通道堆放杂物，影响应急疏散。",
        "reporter": "张伟",
        "due_date": (date.today() + timedelta(days=3)).isoformat(),
        "attachment_url": "https://example.com/demo.jpg",
    }
    data.update(overrides)
    return data


def test_seed_data_available(client):
    response = client.get("/api/hazards", params={"page_size": 100})
    assert response.status_code == 200
    body = response.json()
    assert body["total"] >= 10
    assert body["items"][0]["hazard_no"].startswith("HSE-")


def test_options_endpoint(client):
    options = client.get("/api/hazards/options")
    assert options.status_code == 200
    body = options.json()
    assert "消防安全" in body["types"]
    assert body["levels"] == ["一般", "较大", "重大"]
    assert body["statuses"] == ["待审核", "整改中", "待验收", "已关闭"]


def test_full_business_flow(client):
    created = client.post("/api/hazards", json=_payload())
    assert created.status_code == 201, created.text
    hazard = created.json()
    assert hazard["status"] == "待审核"
    assert hazard["owner"] is None
    assert hazard["is_overdue"] is False
    hazard_id = hazard["id"]

    assigned = client.patch(
        f"/api/hazards/{hazard_id}/assign",
        json={"owner": "李强", "operator": "安全管理员", "comment": "请三日内完成清理"},
    )
    assert assigned.status_code == 200, assigned.text
    assert assigned.json()["status"] == "整改中"
    assert assigned.json()["owner"] == "李强"

    rectified = client.patch(
        f"/api/hazards/{hazard_id}/rectification",
        json={
            "rectification_measure": "清理通道杂物并设置禁放标识",
            "rectification_result": "杂物已清理，禁放标识已张贴。",
            "operator": "李强",
        },
    )
    assert rectified.status_code == 200, rectified.text
    assert rectified.json()["status"] == "待验收"

    closed = client.patch(
        f"/api/hazards/{hazard_id}/acceptance",
        json={"approved": True, "acceptance_comment": "现场复核通过", "operator": "安全管理员"},
    )
    assert closed.status_code == 200, closed.text
    detail = closed.json()
    assert detail["status"] == "已关闭"
    assert [log["action"] for log in detail["logs"]] == [
        "create",
        "assign",
        "submit_rectification",
        "accept",
    ]

    statistics = client.get("/api/hazards/statistics").json()
    assert statistics["status_counts"]["已关闭"] >= 1
    assert statistics["total"] == len(client.get("/api/hazards", params={"page_size": 100}).json()["items"])


def test_acceptance_reject_returns_to_rectifying(client):
    hazard_id = client.post("/api/hazards", json=_payload()).json()["id"]
    client.patch(f"/api/hazards/{hazard_id}/assign", json={"owner": "李强"})
    client.patch(
        f"/api/hazards/{hazard_id}/rectification",
        json={"rectification_measure": "清理通道杂物", "rectification_result": "已清理完毕"},
    )
    rejected = client.patch(
        f"/api/hazards/{hazard_id}/acceptance",
        json={"approved": False, "acceptance_comment": "现场仍有残留纸箱，需继续整改"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "整改中"


def test_invalid_transition_conflict(client):
    hazard_id = client.post("/api/hazards", json=_payload()).json()["id"]
    response = client.patch(
        f"/api/hazards/{hazard_id}/acceptance",
        json={"approved": True, "acceptance_comment": "跳过整改直接验收"},
    )
    assert response.status_code == 409
    assert "待审核" in response.json()["detail"]


def test_missing_hazard_returns_404(client):
    response = client.get("/api/hazards/999999")
    assert response.status_code == 404


def test_validation_errors(client):
    assert client.post("/api/hazards", json=_payload(location="")).status_code == 422
    assert client.post("/api/hazards", json=_payload(hazard_type="未知类型")).status_code == 422
    past = (date.today() - timedelta(days=1)).isoformat()
    assert client.post("/api/hazards", json=_payload(due_date=past)).status_code == 422
    assert (
        client.post("/api/hazards", json=_payload(attachment_url="ftp://bad")).status_code
        == 422
    )
    assert client.get("/api/hazards", params={"page": 0}).status_code == 422


def test_filters_search_and_sorting(client):
    by_status = client.get("/api/hazards", params={"status": "整改中", "page_size": 100}).json()
    assert by_status["total"] > 0
    assert all(item["status"] == "整改中" for item in by_status["items"])

    by_level = client.get("/api/hazards", params={"level": "重大", "page_size": 100}).json()
    assert by_level["total"] > 0
    assert all(item["hazard_level"] == "重大" for item in by_level["items"])

    by_type = client.get("/api/hazards", params={"type": "消防安全", "page_size": 100}).json()
    assert all(item["hazard_type"] == "消防安全" for item in by_type["items"])

    keyword = client.get("/api/hazards", params={"keyword": "消防通道", "page_size": 100}).json()
    assert keyword["total"] >= 1

    sorted_items = client.get(
        "/api/hazards",
        params={"sort_by": "due_date", "sort_order": "asc", "page_size": 100},
    ).json()["items"]
    due_dates = [item["due_date"] for item in sorted_items]
    assert due_dates == sorted(due_dates)

    overdue = client.get("/api/hazards", params={"overdue": True, "page_size": 100}).json()
    assert all(item["is_overdue"] for item in overdue["items"])
