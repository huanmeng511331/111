"""完整业务链路与状态机回归测试（使用独立临时数据库）。"""

import os
import tempfile
from datetime import date, timedelta

from fastapi.testclient import TestClient

_TEMP_DB = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
os.environ["HSE_DB_PATH"] = _TEMP_DB.name

from app.config import DB_PATH  # noqa: E402
from app.main import app  # noqa: E402


def _client() -> TestClient:
    return TestClient(app)


def test_full_closure_flow() -> None:
    due_date = (date.today() + timedelta(days=5)).isoformat()
    with _client() as client:
        created = client.post(
            "/api/hazards",
            json={
                "hazard_type": "消防",
                "hazard_level": "一般",
                "location": "三号库房消防通道",
                "description": "消防通道堆放杂物，影响紧急疏散。",
                "reporter": "测试上报人",
                "due_date": due_date,
            },
        )
        assert created.status_code == 201, created.text
        hazard = created.json()
        assert hazard["status"] == "待审核"
        hazard_id = hazard["id"]

        # 未审核时不允许直接提交整改
        blocked = client.patch(
            f"/api/hazards/{hazard_id}/rectification",
            json={
                "rectification_measure": "清理杂物",
                "rectification_result": "已清理",
                "operator": "测试责任人",
            },
        )
        assert blocked.status_code == 409, blocked.text

        assigned = client.patch(
            f"/api/hazards/{hazard_id}/assign",
            json={"owner": "赵磊（后勤部）", "due_date": due_date, "auditor": "安全管理员"},
        )
        assert assigned.status_code == 200, assigned.text
        assert assigned.json()["status"] == "整改中"

        rectified = client.patch(
            f"/api/hazards/{hazard_id}/rectification",
            json={
                "rectification_measure": "已清理并设置禁放标识",
                "rectification_result": "清理完成并设置禁放标识",
                "operator": "赵磊（后勤部）",
            },
        )
        assert rectified.status_code == 200, rectified.text
        assert rectified.json()["status"] == "待验收"

        rejected = client.patch(
            f"/api/hazards/{hazard_id}/acceptance",
            json={"decision": "reject", "acceptance_comment": "标识不够醒目，请重新整改", "operator": "安全管理员"},
        )
        assert rejected.status_code == 200, rejected.text
        assert rejected.json()["status"] == "整改中"

        client.patch(
            f"/api/hazards/{hazard_id}/rectification",
            json={
                "rectification_measure": "更换大型禁放标识牌",
                "rectification_result": "已更换醒目标识牌",
                "operator": "赵磊（后勤部）",
            },
        )
        closed = client.patch(
            f"/api/hazards/{hazard_id}/acceptance",
            json={"decision": "pass", "acceptance_comment": "现场核查通过，同意关闭", "operator": "安全管理员"},
        )
        assert closed.status_code == 200, closed.text
        assert closed.json()["status"] == "已关闭"

        detail = client.get(f"/api/hazards/{hazard_id}")
        assert detail.status_code == 200
        actions = [log["action"] for log in detail.json()["flow_logs"]]
        assert actions == ["上报隐患", "审核并分派", "提交整改", "验收退回", "提交整改", "验收通过"]


def test_list_filter_and_statistics() -> None:
    with _client() as client:
        listed = client.get("/api/hazards", params={"status": "已关闭", "page": 1, "page_size": 5})
        assert listed.status_code == 200, listed.text
        body = listed.json()
        assert body["page"] == 1 and body["page_size"] == 5
        assert all(item["status"] == "已关闭" for item in body["items"])

        stats = client.get("/api/hazards/statistics")
        assert stats.status_code == 200
        payload = stats.json()
        assert payload["total"] == payload["closed"] + payload["pending_review"] + payload["rectifying"] + payload["pending_acceptance"]
        assert len(payload["trend"]) == 7


def test_validation_rejects_past_due_date() -> None:
    with _client() as client:
        response = client.post(
            "/api/hazards",
            json={
                "hazard_type": "消防",
                "hazard_level": "一般",
                "location": "测试位置",
                "description": "测试描述内容",
                "reporter": "测试人",
                "due_date": (date.today() - timedelta(days=1)).isoformat(),
            },
        )
        assert response.status_code == 422
        assert "整改期限" in response.text


def test_seed_data_present() -> None:
    with _client() as client:
        listed = client.get("/api/hazards", params={"page_size": 100})
        assert listed.status_code == 200
        assert listed.json()["total"] >= 10
        dictionaries = client.get("/api/hazards/dictionaries")
        assert dictionaries.status_code == 200
        assert "消防" in dictionaries.json()["hazard_types"]
