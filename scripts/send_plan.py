#!/usr/bin/env python3
"""晨间计划推送脚本 - 读取 plans/tomorrow.txt 并通过企微API推送

如果 tomorrow.txt 不存在或为空，发送默认提醒。
"""

import os
import json
import urllib.request
import urllib.error
from datetime import datetime, timedelta

WECOM_CORPID = os.environ["WECOM_CORPID"]
WECOM_SECRET = os.environ["WECOM_SECRET"]
WECOM_AGENTID = int(os.environ["WECOM_AGENTID"])
WECOM_USER = os.environ["WECOM_USER"]

PLAN_FILE = "plans/tomorrow.txt"
ARCHIVE_DIR = "plans/archive"


def get_access_token():
    url = f"https://qyapi.weixin.qq.com/cgi-bin/gettoken?corpid={WECOM_CORPID}&corpsecret={WECOM_SECRET}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=10) as resp:
        data = json.loads(resp.read().decode())
    if data.get("errcode") != 0:
        print(f"获取token失败: {data}")
        return None
    return data["access_token"]


def send_text(token, content):
    url = f"https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={token}"
    payload = {
        "touser": WECOM_USER,
        "msgtype": "text",
        "agentid": WECOM_AGENTID,
        "text": {"content": content},
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        result = json.loads(resp.read().decode())
    if result.get("errcode") != 0:
        print(f"发送失败: {result}")
        return False
    print(f"发送成功: {result.get('errmsg')}")
    return True


def get_weekday_cn(date):
    days = ["星期一", "星期二", "星期三", "星期四", "星期五", "星期六", "星期日"]
    return days[date.weekday()]


def main():
    # 读取计划文件
    plan_content = ""
    if os.path.exists(PLAN_FILE):
        with open(PLAN_FILE, "r", encoding="utf-8") as f:
            plan_content = f.read().strip()

    # 如果没有明日计划，发送默认提醒
    if not plan_content:
        today = datetime.now() + timedelta(hours=8)  # UTC+8
        today_str = today.strftime("%Y-%m-%d")
        weekday = get_weekday_cn(today)
        plan_content = (
            f"📋 今日计划\n"
            f"日期：{today_str} {weekday}\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"⚠️ 今日计划尚未设置\n"
            f"昨晚忘记复盘了？今晚来 WorkBuddy 跟我聊聊，我来帮你安排明天的事。"
        )
    else:
        # 把 [日期] 占位符替换为今天的日期
        today = datetime.now() + timedelta(hours=8)
        today_str = today.strftime("%Y-%m-%d")
        weekday = get_weekday_cn(today)
        plan_content = plan_content.replace("[日期]", f"{today_str} {weekday}")

        # 归档已发送的计划
        os.makedirs(ARCHIVE_DIR, exist_ok=True)
        archive_name = f"{ARCHIVE_DIR}/{today_str}.txt"
        with open(archive_name, "w", encoding="utf-8") as f:
            f.write(plan_content)
        print(f"已归档到 {archive_name}")

        # 清空 tomorrow.txt（已发送，下次需要重新生成）
        with open(PLAN_FILE, "w", encoding="utf-8") as f:
            f.write("")

    # 发送消息
    token = get_access_token()
    if token:
        send_text(token, plan_content)


if __name__ == "__main__":
    main()
