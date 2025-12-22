#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Stop Hook - 会话停止时的桌面通知
"""
import sys
import os
import platform
import subprocess
import io

# 在 Windows 上设置 UTF-8 输出编码
if sys.platform == "win32":
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


def send_windows_notification(title: str, message: str) -> bool:
    """发送 Windows 桌面通知"""
    try:
        # 使用 PowerShell 发送 Toast 通知
        ps_script = f"""
$null = [Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType = WindowsRuntime]
$null = [Windows.Data.Xml.Dom.XmlDocument, Windows.Data.Xml.Dom.XmlDocument, ContentType = WindowsRuntime]

$APP_ID = '{{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}}\\WindowsPowerShell\\v1.0\\powershell.exe'

$template = @"
<toast>
    <visual>
        <binding template="ToastText02">
            <text id="1">{title}</text>
            <text id="2">{message}</text>
        </binding>
    </visual>
</toast>
"@

$xml = New-Object Windows.Data.Xml.Dom.XmlDocument
$xml.LoadXml($template)
$toast = New-Object Windows.UI.Notifications.ToastNotification $xml
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier($APP_ID).Show($toast)
"""

        result = subprocess.run(
            ["powershell", "-Command", ps_script],
            capture_output=True,
            text=True,
            timeout=5,
        )

        return result.returncode == 0

    except Exception as e:
        print(f"⚠️  Windows 通知发送失败: {e}", file=sys.stderr)
        return False


def send_macos_notification(title: str, message: str) -> bool:
    """发送 macOS 桌面通知"""
    try:
        applescript = f'display notification "{message}" with title "{title}"'
        result = subprocess.run(
            ["osascript", "-e", applescript],
            capture_output=True,
            text=True,
            timeout=5,
        )

        return result.returncode == 0

    except Exception as e:
        print(f"⚠️  macOS 通知发送失败: {e}", file=sys.stderr)
        return False


def send_linux_notification(title: str, message: str) -> bool:
    """发送 Linux 桌面通知"""
    try:
        result = subprocess.run(
            ["notify-send", title, message],
            capture_output=True,
            text=True,
            timeout=5,
        )

        return result.returncode == 0

    except Exception as e:
        print(f"⚠️  Linux 通知发送失败: {e}", file=sys.stderr)
        return False


def main():
    """发送会话停止通知"""
    title = "Claude Code 会话已停止"
    message = "AI 广告代投系统 - 会话已结束"

    system = platform.system()

    print("=" * 80)
    print("👋 会话停止 Hook")
    print("=" * 80)
    print()

    success = False

    if system == "Windows":
        success = send_windows_notification(title, message)
    elif system == "Darwin":  # macOS
        success = send_macos_notification(title, message)
    elif system == "Linux":
        success = send_linux_notification(title, message)
    else:
        print(f"⚠️  不支持的操作系统: {system}")

    if success:
        print("✅ 桌面通知已发送")
    else:
        print("⚠️  桌面通知发送失败（这不影响会话停止）")

    print()
    print("=" * 80)
    print("感谢使用 Claude Code！")
    print("=" * 80)
    print()

    return 0


if __name__ == "__main__":
    sys.exit(main())
