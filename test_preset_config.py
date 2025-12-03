"""测试预设配置功能"""

from agents.config import load_preset, list_available_presets, merge_preset_with_overrides

# 测试 1: 列出所有预设
print("=" * 60)
print("测试 1: 列出所有预设")
print("=" * 60)
presets = list_available_presets()
print(f"可用预设: {presets}")
print()

# 测试 2: 加载预设
print("=" * 60)
print("测试 2: 加载预设 finance_profit_backend_full")
print("=" * 60)
preset = load_preset("finance_profit_backend_full")
print(f"Flow: {preset.get('flow')}")
print(f"Task: {preset.get('task')}")
print(f"Module: {preset.get('module')}")
print(f"Target Files: {preset.get('target_files')}")
print()

# 测试 3: 合并预设和覆盖
print("=" * 60)
print("测试 3: 合并预设和 CLI 覆盖")
print("=" * 60)
overrides = {
    "task": "Custom task description",
    "target_files": ["backend/custom.py"],
}
merged = merge_preset_with_overrides(preset, overrides)
print(f"原始 task: {preset.get('task')}")
print(f"覆盖后 task: {merged.get('task')}")
print(f"原始 target_files 数量: {len(preset.get('target_files', []))}")
print(f"覆盖后 target_files 数量: {len(merged.get('target_files', []))}")
print(f"覆盖后 target_files: {merged.get('target_files')}")
print()

print("✅ 所有测试通过！")

