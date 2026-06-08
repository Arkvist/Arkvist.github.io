#!/usr/bin/env python3
"""晨间计划推送脚本 - 读取 plans/tomorrow.txt 并通过企微群机器人 Webhook 推送

使用 Webhook，无需 IP 白名单，支持云端运行。
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# 企微群机器人 Webhook 地址
WEBHOOK_URL = os.environ["WECOM_WEBHOOK_URL"]

PLAN_FILE = "plans/tomorrow.txt"
ARCHIVE_DIR = "plans/archive"


def send_markdown(content):
    """通过 Webhook 发送 markdown 消息"""
    payload = {
        "msgtype": "markdown",
        "markdown": {"content": content}
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            result = json.loads(resp.read().decode())
        if result.get("errcode") != 0:
            print(f"发送失败: {result}")
            return False
        print(f"发送成功: {result}")
        return True
    except Exception as e:
        print(f"发送异常: {e}")
        return False


def get_weekday_cn(date):
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return days[date.weekday()]


def main():
    # 读取计划文件
    plan_content = ""
    if os.path.exists(PLAN_FILE):
        with open(PLAN_FILE, "r", encoding="utf-8") as f:
            plan_content = f.read().strip()

    today = datetime.now() + timedelta(hours=8)  # UTC+8
    today_str = today.strftime("%Y-%m-%d")
    weekday = get_weekday_cn(today)

    if not plan_content:
        # 没有明日计划，发送默认提醒
        content = (
            f"📋 今日计划\n"
            f"日期：{today_str} {weekday}\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"⚠️ 今日计划尚未设置\n"
            f"昨晚忘记复盘了？今晚来 WorkBuddy 跟我聊聊，我来帮你安排明天的事。"
        )
    else:
        # 替换占位符，用 markdown 格式发送
        content = plan_content.replace("[日期]", f"{today_str} {weekday}")

        # 归档已发送的计划
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        archive_name = f"{ARCHIVE_DIR}/{today_str}.txt"
        with open(archive_name, "w", encoding="utf-8") as f:
            f.write(content)
        print(f"已归档到 {archive_name}")

        # 清空 tomorrow.txt（已发送，下次需要重新生成）
        with open(PLAN_FILE, "w", encoding="utf-8") as f:
            f.write("")

    # 发送消息
    send_markdown(content)


if __name__ == "__main__":
    main()
