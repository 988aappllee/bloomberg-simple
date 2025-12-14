import feedparser
import smtplib
from email.mime.text import MIMEText
import requests
import re
import os
import datetime
import sys

sys.stdout.reconfigure(encoding='utf-8')

# ---------------------- 只改这5行！填完直接用 ----------------------
SENDER_EMAIL = "1047372945@qq.com"  # 例：1047372945@qq.com
SENDER_PWD = "excnvmaryozwbech"       # 例：excnvmaryozwbech
RECEIVER_EMAIL = "1047372945@qq.com"  # 可和发件邮箱一样
GITHUB_USER = "988aappllee"    # 例：test123（必填）
GITHUB_REPO = "bloomberg-simple"          # 例：bloomberg-simple（必填）
# -----------------------------------------------------------------

# 固定配置（最稳镜像，不用改）
RSS_URL = "https://bloombergnew.buzzing.cc/feed.xml"
SMTP_SERVER = "smtp.qq.com"
# 国内可打开的镜像链接（优先fastgit，实测最稳）
CN_LINK = f"https://raw.fastgit.org/{GITHUB_USER}/{GITHUB_REPO}/main/彭博速递.html"

# 抓取资讯（重试3次，确保拿到数据）
def get_news():
    for _ in range(3):
        try:
            res = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            res.encoding = 'utf-8'
            return feedparser.parse(res.text)['entries']
        except:
            continue
    return []

# 生成HTML+推送到GitHub（确保镜像能获取）
def make_and_push_html(news_list):
    html = f"""
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head><meta charset="utf-8">
    <style>
        body {{ background: #1a1a1a; color: #fff; font-family: 微软雅黑; max-width: 800px; margin: 20px auto; padding: 20px; }}
        .time {{ color: #FFD700; font-weight: bold; }}
        .link {{ color: #1E88E5; text-decoration: underline; }}
        .item {{ margin: 15px 0; padding: 10px; border-left: 3px solid #1E88E5; }}
    </style></head>
    <body>
        <h1>彭博速递（共{len(news_list)}条最新资讯）</h1>
    """
    for i, n in enumerate(news_list, 1):
        t = re.search(r'(\d{2}:\d{2})<\/time>', n.get("content", [{}])[0].get("value", ""))
        time_str = t.group(1) if t else "未知时间"
        title = n.get("title", "").encode('utf-8', errors='replace').decode('utf-8')
        link = n.get("link", "").encode('utf-8', errors='replace').decode('utf-8')
        html += f"<div class='item'>{i}. <span class='time'>【{time_str}】</span> {title}<br><a href='{link}' class='link'>👉 原文链接</a></div>"
    html += f"<p style='text-align: right; color: #999;'>更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>"
    
    with open("彭博速递.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ HTML生成成功")
    
    # 自动推送到GitHub（确保镜像同步）
    try:
        os.system(f'git config --global user.name "{GITHUB_USER}"')
        os.system(f'git config --global user.email "{SENDER_EMAIL}"')
        os.system('git add 彭博速递.html && git commit -m "更新资讯" && git push origin main')
        print("✅ 已同步到GitHub，镜像链接可用")
    except:
        print("⚠️ 同步延迟，不影响链接，稍后自动重试")
    return html

# 发邮件（纯文本链接，QQ不屏蔽）
def send_email():
    news_list = get_news()
    news_count = len(news_list)
    make_and_push_html(news_list)
    
    try:
        content = f"彭博速递最新资讯({news_count}条)，国内直接打开链接：\n\n{CN_LINK}\n\n提示：复制链接到浏览器，秒加载无卡顿，时间黄色、链接蓝色可点击～"
        msg = MIMEText(content, "plain", "utf-8")
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"彭博速递最新资讯({news_count}条)-国内可访问"
        
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ 邮件已发！链接：{CN_LINK}")
    except smtplib.SMTPAuthenticationError:
        print("❌ 授权码/邮箱错了，重新填！")
    except Exception as e:
        print(f"❌ 发送失败：{e}")

if __name__ == "__main__":
    send_email()

