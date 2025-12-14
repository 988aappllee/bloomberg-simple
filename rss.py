import feedparser
import smtplib
from email.mime.text import MIMEText
import requests
import re
import datetime
import sys
import base64

# 全局编码防乱码
sys.stdout.reconfigure(encoding='utf-8')

# ---------------------- 已填好你的信息，不用改 ----------------------
SENDER_EMAIL = "1047372945@qq.com"  # 发件QQ邮箱
SENDER_PWD = "excnvmaryozwbech"    # QQ邮箱16位授权码
RECEIVER_EMAIL = "1047372945@qq.com"  # 收件邮箱
# -------------------------------------------------------------------

# 生成可点击的Data URI链接
def make_clickable_data_uri(html_content):
    html_bytes = html_content.encode('utf-8')
    base64_str = base64.b64encode(html_bytes).decode('utf-8')
    # 直接生成邮件里可点击的链接
    return f"data:text/html;base64,{base64_str}"

# 抓取彭博资讯
def get_news():
    for _ in range(3):
        try:
            res = requests.get("https://bloombergnew.buzzing.cc/feed.xml", headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            res.encoding = 'utf-8'
            return feedparser.parse(res.text)['entries']
        except:
            continue
    return []

# 生成资讯HTML
def make_html(news_list):
    if not news_list:
        return "<h2 style='color: #FFD700;'>暂无彭博资讯</h2>"
    
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head><meta charset="utf-8">
    <style>
        body {{ background: #1a1a1a; color: #fff; font-family: 微软雅黑; max-width: 800px; margin: 20px auto; padding: 20px; }}
        .time {{ color: #FFD700; font-weight: bold; }}
        .link {{ color: #1E88E5; text-decoration: underline; }}
        .item {{ margin: 15px 0; padding: 10px; border-left: 3px solid #1E88E5; }}
        h1 {{ color: #2E4057; text-align: center; }}
    </style></head>
    <body>
        <h1>彭博速递（共{len(news_list)}条）</h1>
    """
    for i, n in enumerate(news_list, 1):
        t = re.search(r'(\d{2}:\d{2})<\/time>', n.get("content", [{}])[0].get("value", ""))
        time_str = t.group(1) if t else "未知时间"
        title = n.get("title", "").encode('utf-8', errors='replace').decode('utf-8')
        link = n.get("link", "").encode('utf-8', errors='replace').decode('utf-8')
        html += f"<div class='item'>{i}. <span class='time'>【{time_str}】</span> {title}<br><a href='{link}' class='link'>👉 原文</a></div>"
    html += f"<p style='text-align: right; color: #999;'>更新：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p></body></html>"
    return html

# 发送带可点击链接的邮件
def send_email():
    news_list = get_news()
    news_count = len(news_list)
    html_content = make_html(news_list)
    clickable_link = make_clickable_data_uri(html_content)

    try:
        # 邮件里直接放可点击的蓝色链接
        email_html = f"""
        <p>彭博速递最新资讯来啦！本次共{news_count}条：</p>
        <p style="font-size: 16px;">
            🔗 <a href="{clickable_link}" target="_blank" style="color: #1E88E5; font-weight: bold;">点击直接打开资讯页面（国内秒开）</a>
        </p>
        <p style="color: #999; font-size: 12px;">提示：点击后直接在浏览器打开，不用注册任何东西～</p>
        """
        msg = MIMEText(email_html, "html", "utf-8")
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"彭博速递（{news_count}条）- 点击即看"

        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("✅ 邮件发好了！邮箱里点链接直接看～")
    except Exception as e:
        print(f"❌ 发送失败：{e}")

if __name__ == "__main__":
    send_email()

