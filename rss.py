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

# ---------------------- 已填好的信息（替换为你真实的授权码/邮箱） ----------------------
SENDER_EMAIL = "1047372945@qq.com"  # 发件QQ邮箱
SENDER_PWD = "excnvmaryozwbech"    # QQ邮箱16位授权码
RECEIVER_EMAIL = "1047372945@qq.com"  # 收件邮箱（和发件邮箱一致）
# -------------------------------------------------------------------------------------

# 固定配置
RSS_URL = "https://bloombergnew.buzzing.cc/feed.xml"
HTML_FILE = "彭博速递.html"
SMTP_SERVER = "smtp.qq.com"
LAST_LINK_FILE = "last_link.txt"

# 检查是否有新资讯（对比最新链接）
def has_new_news():
    try:
        res = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
        news_list = feedparser.parse(res.content).entries
        if not news_list:
            return False, None
        
        latest_link = news_list[0]["link"]
        # 首次运行/无历史记录
        if not os.path.exists(LAST_LINK_FILE):
            with open(LAST_LINK_FILE, 'w', encoding='utf-8') as f:
                f.write(latest_link)
            return True, news_list
        
        # 对比历史链接判断更新
        with open(LAST_LINK_FILE, 'r', encoding='utf-8') as f:
            old_link = f.read().strip()
        if latest_link != old_link:
            with open(LAST_LINK_FILE, 'w', encoding='utf-8') as f:
                f.write(latest_link)
            return True, news_list
        else:
            return False, None
    except Exception as e:
        print(f"检查资讯更新失败：{e}")
        return False, None

# 生成HTML文件（黄色时间+蓝色链接）
def make_html(news_list):
    if not news_list:
        return False
    
    # HTML样式与内容拼接
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
    # 拼接所有资讯
    for i, n in enumerate(news_list, 1):
        # 提取时间
        t = re.search(r'(\d{2}:\d{2})<\/time>', n.get("content", [{}])[0].get("value", ""))
        time = t.group(1) if t else n.get("updated", "")[:10].split('-')[1:]
        time = ":".join(time) if isinstance(time, list) else time
        # 拼接单条资讯
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
    print(f"✅ HTML文件生成成功，共{len(news_list)}条资讯")
    return True

# 发送邮件（修复附件bin问题+编码+邮件头）
def send_email():
    if not os.path.exists(HTML_FILE):
        print("❌ 未找到HTML文件，跳过邮件发送")
        return
    
    try:
        msg = MIMEMultipart()
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = "彭博速递最新资讯（全部内容）"  # 修复邮件头嵌入问题

        # 邮件正文
        body = MIMEText("点击附件查看彭博资讯全部内容，时间黄色高亮、链接蓝色可点击～", "html", "utf-8")
        msg.attach(body)

        # 添加HTML附件（修复MIME类型，解决bin问题）
        with open(HTML_FILE, "rb") as f:
            part = MIMEBase("text", "html")  # 改为HTML专属MIME类型，不再是二进制流
            part.set_payload(f.read())
            encoders.encode_base64(part)
            # 双文件名配置，确保QQ邮箱正确识别为HTML
            part.add_header(
                "Content-Disposition",
                f"attachment; filename*=UTF-8''{HTML_FILE}; filename={HTML_FILE}"
            )
            msg.attach(part)

        # 拆分SMTP调用，避免编码/属性错误
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("✅ 邮件发送成功，附件为HTML文件！")
    except smtplib.SMTPAuthenticationError:
        print("❌ 邮件登录失败：请检查QQ邮箱授权码或账号是否正确")
    except Exception as e:
        print(f"❌ 邮件发送失败：{str(e)}")

# 核心运行逻辑
if __name__ == "__main__":
    has_new, news_list = has_new_news()
    if has_new and news_list:
        if make_html(news_list):
            send_email()
            print(f"✅ 全流程完成，共推送{len(news_list)}条资讯，查收邮箱！")
    else:
        print("❌ 暂无新资讯，无需推送")

