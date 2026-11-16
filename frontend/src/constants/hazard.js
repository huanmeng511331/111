// 与后端 app/models/enums.py 保持一致；后端 /api/hazards/options 为权威来源。
export const TYPE_OPTIONS = [
  '消防安全',
  '电气安全',
  '设备设施',
  '作业行为',
  '职业健康',
  '环境环保',
  '其他'
]

export const LEVEL_OPTIONS = ['一般', '较大', '重大']

export const STATUS_OPTIONS = ['待审核', '整改中', '待验收', '已关闭']

export const STATUS_META = {
  待审核: { tag: 'warning', hint: '等待安全管理人员审核分派' },
  整改中: { tag: 'primary', hint: '责任人正在整改' },
  待验收: { tag: 'info', hint: '等待安全管理人员验收' },
  已关闭: { tag: 'success', hint: '隐患已验收关闭' }
}

export const LEVEL_META = {
  一般: { tag: 'info' },
  较大: { tag: 'warning' },
  重大: { tag: 'danger' }
}
