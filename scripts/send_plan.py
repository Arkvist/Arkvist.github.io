#!/usr/bin/env python3
"""晨间计划推送脚本 - 读取 plans/tomorrow.txt 并通过企微群机器人 Webhook 推送

使用 Webhook，无需 IP 白名单，支持云端运行。
自动拆分超长消息，逐条发送。
"""

import os
import json
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta

# 企微群机器人 Webhook 地址
WEBHOOK_URL = os.environ["WECOM_WEBHOOK_URL"]

PLAN_FILE = "plans/tomorrow.txt"
ARCHIVE_DIR = "plans/archive"

# 每条消息最大字符数（text 类型限制 2048）
MAX_CHARS = 2000


def send_text(content):
    """通过 Webhook 发送纯文本消息"""
    payload = {
        "msgtype": "text",
        "text": {"content": content}
    }
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(WEBHOOK_URL, data=data, headers={"Content-Type": "application/json; charset=utf-8"})
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


def split_message(content, max_chars=MAX_CHARS):
    """按段落拆分超长消息，每段不超过 max_chars 字符
    
    拆分逻辑：
    1. 按空行分段落
    2. 尽量把相邻段落合并到同一条消息
    3. 单个段落超长时按行再拆
    """
    # 按空行分段
    paragraphs = [p.strip() for p in content.split("\n\n") if p.strip()]
    
    chunks = []
    current_chunk = ""
    
    for para in paragraphs:
        # 如果单个段落就超长，按行拆
        if len(para) > max_chars:
            # 先把当前积攒的内容存起来
            if current_chunk:
                chunks.append(current_chunk)
                current_chunk = ""
            # 按行拆这个超长段落
            lines = para.split("\n")
            for line in lines:
                if len(current_chunk) + len(line) + 1 > max_chars:
                    if current_chunk:
                        chunks.append(current_chunk)
                    current_chunk = line
                else:
                    current_chunk = current_chunk + "\n" + line if current_chunk else line
        # 加上这个段落不超长
        elif len(current_chunk) + len(para) + 2 <= max_chars:
            current_chunk = current_chunk + "\n\n" + para if current_chunk else para
        # 超长了，当前积攒的存起来，新开一段
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = para
    
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks


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
            f"今日计划\n"
            f"日期：{today_str} {weekday}\n\n"
            f"━━━━━━━━━━━━━━━\n\n"
            f"今日计划尚未设置\n"
            f"昨晚忘记复盘了？今晚来 WorkBuddy 跟我聊聊，我来帮你安排明天的事。"
        )
    else:
        # 替换占位符
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

    # 拆分消息
    chunks = split_message(content)
    total = len(chunks)
    
    print(f"消息拆分为 {total} 条，开始发送...")
    
    for i, chunk in enumerate(chunks, 1):
        # 多条消息加序号
        if total > 1:
            final_content = f"[{i}/{total}]\n\n{chunk}"
        else:
            final_content = chunk
        
        success = send_text(final_content)
        if not success:
            print(f"第 {i}/{total} 条发送失败，继续尝试下一条")
        
        # 多条消息间隔1秒，避免频率限制
        if i < total:
            time.sleep(1)
    
    print(f"全部发送完成，共 {total} 条")


if __name__ == "__main__":
    main()
