"""首次启动时写入演示数据（全为模拟数据，不含真实生产信息）。"""

from datetime import date, timedelta
from typing import Any

from app.db import get_connection
from app.models.hazard import (
    STATUS_CLOSED,
    STATUS_PENDING_ACCEPTANCE,
    STATUS_PENDING_REVIEW,
    STATUS_RECTIFYING,
    add_flow_log,
    next_hazard_no,
)

DEMO_HAZARDS = [
    {
        "hazard_type": "消防",
        "hazard_level": "较大",
        "location": "一号厂房东侧消防通道",
        "description": "消防通道堆放包装箱，影响人员疏散和消防车通行。",
        "reporter": "陈晨",
        "owner": "赵磊（后勤部）",
        "due_offset": 3,
        "status": STATUS_PENDING_REVIEW,
        "created_offset": 0,
        "image_url": "https://example.com/demo/fire-exit.png",
        "rectification_measure": None,
        "rectification_result": None,
        "acceptance_comment": None,
    },
    {
        "hazard_type": "用电",
        "hazard_level": "重大",
        "location": "二号厂房配电室",
        "description": "配电柜缺少接地保护，柜门未上锁，存在触电风险。",
        "reporter": "刘海",
        "owner": "张伟（设备部）",
        "due_offset": 1,
        "status": STATUS_RECTIFYING,
        "created_offset": 2,
        "image_url": None,
        "rectification_measure": "补装接地线并加装柜门锁具。",
        "rectification_result": None,
        "acceptance_comment": None,
    },
    {
        "hazard_type": "作业行为",
        "hazard_level": "一般",
        "location": "检修车间焊接工位",
        "description": "动火作业未办理作业票，现场未配置灭火器。",
        "reporter": "周敏",
        "owner": "王敏（生产一部）",
        "due_offset": 2,
        "status": STATUS_PENDING_ACCEPTANCE,
        "created_offset": 4,
        "image_url": None,
        "rectification_measure": "补办动火作业票，配置两具干粉灭火器。",
        "rectification_result": "作业票已补办并归档，灭火器已配置到位。",
        "acceptance_comment": None,
    },
    {
        "hazard_type": "设备设施",
        "hazard_level": "较大",
        "location": "原料仓库叉车通道",
        "description": "叉车限速标识缺失，通道转角存在视觉盲区。",
        "reporter": "陈晨",
        "owner": "李强（安全部）",
        "due_offset": -2,
        "status": STATUS_RECTIFYING,
        "created_offset": 9,
        "image_url": None,
        "rectification_measure": "加装限速标识与转角反光镜。",
        "rectification_result": None,
        "acceptance_comment": None,
    },
    {
        "hazard_type": "环境",
        "hazard_level": "一般",
        "location": "厂区污水处理站",
        "description": "污水采样口周边存在积液，缺少防渗托盘。",
        "reporter": "孙悦",
        "owner": "赵磊（后勤部）",
        "due_offset": -6,
        "status": STATUS_CLOSED,
        "created_offset": 12,
        "image_url": None,
        "rectification_measure": "增设防渗托盘并定期清理积液。",
        "rectification_result": "防渗托盘已安装，现场清理完成。",
        "acceptance_comment": "现场核查通过，同意关闭。",
    },
    {
        "hazard_type": "职业健康",
        "hazard_level": "较大",
        "location": "喷涂车间",
        "description": "喷漆岗位未按规定佩戴防毒面具，通风设施运行不稳定。",
        "reporter": "刘海",
        "owner": "王敏（生产一部）",
        "due_offset": 5,
        "status": STATUS_RECTIFYING,
        "created_offset": 3,
        "image_url": None,
        "rectification_measure": "补充防毒面具并检修通风机组。",
        "rectification_result": None,
        "acceptance_comment": None,
    },
    {
        "hazard_type": "消防",
        "hazard_level": "一般",
        "location": "办公楼三层走廊",
        "description": "应急照明灯损坏，疏散指示标识不亮。",
        "reporter": "孙悦",
        "owner": "李强（安全部）",
        "due_offset": -1,
        "status": STATUS_PENDING_ACCEPTANCE,
        "created_offset": 6,
        "image_url": None,
        "rectification_measure": "更换应急照明灯具并测试疏散指示。",
        "rectification_result": "灯具已更换，断电测试正常。",
        "acceptance_comment": None,
    },
    {
        "hazard_type": "用电",
        "hazard_level": "一般",
        "location": "食堂操作间",
        "description": "插座靠近水池且无防水罩，存在漏电风险。",
        "reporter": "周敏",
        "owner": "赵磊（后勤部）",
        "due_offset": -10,
        "status": STATUS_CLOSED,
        "created_offset": 15,
        "image_url": None,
        "rectification_measure": "更换为防水插座并加装防水罩。",
        "rectification_result": "防水插座更换完成，已通电测试。",
        "acceptance_comment": "整改符合要求，隐患关闭。",
    },
    {
        "hazard_type": "设备设施",
        "hazard_level": "重大",
        "location": "锅炉房",
        "description": "压力表超过检定有效期，安全阀未按期校验。",
        "reporter": "陈晨",
        "owner": "张伟（设备部）",
        "due_offset": 7,
        "status": STATUS_PENDING_REVIEW,
        "created_offset": 1,
        "image_url": None,
        "rectification_measure": None,
        "rectification_result": None,
        "acceptance_comment": None,
    },
    {
        "hazard_type": "作业行为",
        "hazard_level": "一般",
        "location": "成品库装卸平台",
        "description": "装卸人员未系安全带进行高处作业。",
        "reporter": "孙悦",
        "owner": "王敏（生产一部）",
        "due_offset": -3,
        "status": STATUS_CLOSED,
        "created_offset": 11,
        "image_url": None,
        "rectification_measure": "组织高处作业培训并配置双钩安全带。",
        "rectification_result": "培训完成 12 人，安全带已发放到位。",
        "acceptance_comment": "复查无违章，同意关闭。",
    },
]


def _created_text(offset_days: int) -> str:
    target = date.today() - timedelta(days=offset_days)
    return f"{target.isoformat()} 09:30:00"


def _seed_flow(connection: Any, hazard_id: int, hazard: dict, created_at: str) -> None:
    """按状态补齐演示用的流转记录。"""
    reporter = hazard["reporter"]
    connection.execute(
        "UPDATE hazards SET created_at = ?, updated_at = ? WHERE id = ?",
        (created_at, created_at, hazard_id),
    )
    add_flow_log(
        connection,
        hazard_id,
        action="上报隐患",
        from_status=None,
        to_status=STATUS_PENDING_REVIEW,
        operator=reporter,
        comment=hazard["description"],
    )
    if hazard["status"] == STATUS_PENDING_REVIEW:
        return
    add_flow_log(
        connection,
        hazard_id,
        action="审核并分派",
        from_status=STATUS_PENDING_REVIEW,
        to_status=STATUS_RECTIFYING,
        operator="安全管理员",
        comment=f"分派给 {hazard['owner']}",
    )
    if hazard["status"] == STATUS_RECTIFYING:
        return
    add_flow_log(
        connection,
        hazard_id,
        action="提交整改",
        from_status=STATUS_RECTIFYING,
        to_status=STATUS_PENDING_ACCEPTANCE,
        operator=hazard["owner"] or "责任人",
        comment=hazard["rectification_result"],
    )
    if hazard["status"] == STATUS_CLOSED:
        add_flow_log(
            connection,
            hazard_id,
            action="验收通过",
            from_status=STATUS_PENDING_ACCEPTANCE,
            to_status=STATUS_CLOSED,
            operator="安全管理员",
            comment=hazard["acceptance_comment"],
        )


def seed_demo_data() -> int:
    """仅在隐患表为空时写入演示数据，返回写入条数。"""
    with get_connection() as connection:
        existing = connection.execute("SELECT COUNT(*) AS total FROM hazards").fetchone()["total"]
        if existing:
            return 0
        for hazard in DEMO_HAZARDS:
            hazard_no = next_hazard_no(connection)
            created_at = _created_text(hazard["created_offset"])
            due_date = (date.today() + timedelta(days=hazard["due_offset"])).isoformat()
            cursor = connection.execute(
                "INSERT INTO hazards (hazard_no, hazard_type, hazard_level, location, description, "
                "reporter, owner, due_date, status, rectification_measure, rectification_result, "
                "acceptance_comment, image_url, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    hazard_no,
                    hazard["hazard_type"],
                    hazard["hazard_level"],
                    hazard["location"],
                    hazard["description"],
                    hazard["reporter"],
                    hazard["owner"],
                    due_date,
                    hazard["status"],
                    hazard["rectification_measure"],
                    hazard["rectification_result"],
                    hazard["acceptance_comment"],
                    hazard["image_url"],
                    created_at,
                    created_at,
                ),
            )
            _seed_flow(connection, int(cursor.lastrowid), hazard, created_at)
    return len(DEMO_HAZARDS)
