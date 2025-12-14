import feedparser
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import requests
import re
import os
import datetime

# ---------------------- 只改这3行！----------------------
SENDER_EMAIL = "你的QQ邮箱@qq.com"  # 例：1047372945@qq.com
SENDER_PWD = "你的16位授权码"       # 例：excnvmaryozwbech
RECEIVER_EMAIL = "收件邮箱@qq.com"  # 可和发件邮箱一样
# -------------------------------------------------------

# 固定配置（不用改）
RSS_URL = "https://bloombergnew.buzzing.cc/feed.xml"
HTML_FILE = "彭博速递.html"
SMTP_SERVER = "smtp.qq.com"
LAST_LINK_FILE = "last_link.txt"  # 新增：记录最后一次推送的最新资讯链接

# 检查是否有新资讯（核心：对比最新链接判断是否更新）
def has_new_news():
    try:
        res = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        news_list = feedparser.parse(res.content).entries
        if not news_list:
            return False, None
        # 最新资讯的链接（唯一标识）
        latest_link = news_list[0]["link"]
        # 首次运行/无历史记录 → 视为有新资讯
        if not os.path.exists(LAST_LINK_FILE):
            with open(LAST_LINK_FILE, 'w', encoding='utf-8') as f:
                f.write(latest_link)
            return True, news_list
        # 读取历史链接，对比是否更新
        with open(LAST_LINK_FILE, 'r', encoding='utf-8') as f:
            old_link = f.read().strip()
        if latest_link != old_link:
            # 更新历史链接为最新
            with open(LAST_LINK_FILE, 'w', encoding='utf-8') as f:
                f.write(latest_link)
            return True, news_list
        else:
            return False, None
    except Exception as e:
        print(f"检查资讯更新失败：{e}")
        return False, None

# 生成HTML（黄色时间+蓝色链接，包含全部资讯）
def make_html(news_list):
    if not news_list:
        return False
    # HTML样式（固定，不用改）
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="UTF-8">
        <style>
            body {{ background: #1a1a1a; color: #fff; font-family: 微软雅黑; max-width: 800px; margin: 20px auto; }}
            .time {{ color: #FFD700; font-weight: bold; }}
            .link {{ color: #1E88E5; text-decoration: underline; }}
            .item {{ margin: 15px 0; padding: 10px; border-left: 3px solid #1E88E5; }}
        </style>
    </head>
    <body>
        <h1>彭博速递（共{len(news_list)}条最新资讯）</h1>
    """
    # 拼接全部资讯
    for i, n in enumerate(news_list, 1):
        # 提取时间
        t = re.search(r'(\d{2}:\d{2})<\/time>', n.get("content", [{}])[0].get("value", ""))
        time = t.group(1) if t else n.get("updated", "")[:10].split('-')[1:]
        time = ":".join(time) if isinstance(time, list) else time
        # 拼接内容
        html += f"""
        <div class="item">
            {i}. <span class="time">【{time}】</span> {n["title"]}
            <br><a href="{n['link']}" class="link">👉 原文链接</a>
        </div>
        """
    html += f"<p style='text-align: right; color: #999;'>更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>"
    # 保存HTML文件
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    return True

# 发邮件（带HTML附件）
def send_email():
    if not os.path.exists(HTML_FILE):
        return
    msg = MIMEMultipart()
    msg["From"] = SENDER_EMAIL
    msg["To"] = RECEIVER_EMAIL
    msg["Subject"] = "彭博速递最新资讯（全部内容）"
    # 正文
    msg.attach(MIMEText("点击附件查看彭博资讯全部内容，时间黄色、链接蓝色可点击～", "html"))
    # 附件
    with open(HTML_FILE, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", f"attachment; filename={HTML_FILE}")
        msg.attach(part)
    # 发送
    smtplib.SMTP_SSL(SMTP_SERVER, 465).login(SENDER_EMAIL, SENDER_PWD).sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())

# 核心运行（有更新才推送全部内容）
if __name__ == "__main__":
    has_new, news_list = has_new_news()
    if has_new and news_list:
        if make_html(news_list):
            send_email()
            print(f"✅ 成功推送{len(news_list)}条最新资讯，查收邮箱～")
    else:
        print("❌ 暂无新资讯，无需推送")

