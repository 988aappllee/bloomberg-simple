import feedparser
import smtplib
from email.mime.text import MIMEText
import requests
import re
import os
import datetime
import sys
import subprocess

# 全局编码设置
sys.stdout.reconfigure(encoding='utf-8')

# ---------------------- 替换为你的信息 ----------------------
SENDER_EMAIL = "1047372945@qq.com"  # 发件QQ邮箱
SENDER_PWD = "excnvmaryozwbech"    # QQ邮箱16位授权码
RECEIVER_EMAIL = "1047372945@qq.com"  # 收件邮箱
GITHUB_USER = "988aappllee"    # 例：zhangsan（GitHub主页的用户名）
GITHUB_REPO = "bloomberg-simple"   # 你的仓库名（如bloomberg-simple）
# -----------------------------------------------------------

# 固定配置
RSS_URL = "https://bloombergnew.buzzing.cc/feed.xml"
HTML_FILE = "彭博速递.html"
SMTP_SERVER = "smtp.qq.com"
# GitHub Pages基础链接（国内可访问）
PAGE_LINK = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/{HTML_FILE}"

# 抓取资讯（重试5次）
def get_news():
    news_list = []
    for _ in range(5):
        try:
            res = requests.get(RSS_URL, headers={"User-Agent": "Mozilla/5.0"}, timeout=30)
            res.encoding = 'utf-8'
            news_list = feedparser.parse(res.text)['entries']
            if news_list:
                print(f"✅ 抓取成功，共{len(news_list)}条资讯")
                break
        except Exception as e:
            print(f"⚠️ 第{_+1}次抓取失败：{e}")
            continue
    return news_list

# 生成HTML文件（防乱码）
def make_html(news_list):
    # 兜底：无资讯时的提示
    if not news_list:
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head><meta charset="utf-8"><title>彭博速递</title></head>
        <body><h1>暂无彭博资讯（资讯源暂时不可用）</h1></body>
        </html>
        """
    else:
        # 生成带资讯的HTML
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
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
        for i, n in enumerate(news_list, 1):
            t = re.search(r'(\d{2}:\d{2})<\/time>', n.get("content", [{}])[0].get("value", ""))
            time_str = t.group(1) if t else "未知时间"
            title = n.get("title", "").encode('utf-8', errors='replace').decode('utf-8')
            link = n.get("link", "").encode('utf-8', errors='replace').decode('utf-8')
            html += f"""
            <div class="item">
                {i}. <span class="time">【{time_str}】</span> {title}
                <br><a href="{link}" class="link">👉 原文链接</a>
            </div>
            """
        html += f"<p style='text-align: right; color: #999;'>更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>"
    
    # 保存HTML文件
    with open(HTML_FILE, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"✅ HTML文件生成成功：{HTML_FILE}")
    return True

# 推送HTML文件到GitHub仓库（确保Pages能获取）
def push_to_github():
    try:
        # 执行Git命令推送文件
        subprocess.run(["git", "config", "--global", "user.name", GITHUB_USER], check=True)
        subprocess.run(["git", "config", "--global", "user.email", SENDER_EMAIL], check=True)
        subprocess.run(["git", "add", HTML_FILE], check=True)
        subprocess.run(["git", "commit", "-m", f"更新彭博资讯 {datetime.datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print(f"✅ HTML文件已推送到GitHub，Pages链接：{PAGE_LINK}")
        return True
    except Exception as e:
        print(f"⚠️ 推送文件到GitHub失败（不影响链接访问，下次运行会重试）：{e}")
        return False

# 发送邮件（带国内可访问的链接，无附件）
def send_email_with_link(news_count):
    try:
        msg = MIMEText(f"""
        <p>彭博速递最新资讯已更新！本次共推送{news_count}条（点击下方链接直接查看）：</p>
        <p>🔗 <a href="{PAGE_LINK}" target="_blank" style="color: #1E88E5; font-size: 16px;">{PAGE_LINK}</a></p>
        <p>提示：链接国内可直接访问，无需下载附件，点击即可查看黄色时间、蓝色链接的资讯内容～</p>
        """, "html", "utf-8")
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"彭博速递最新资讯（{news_count}条）- 国内可访问链接"

        # 发送邮件
        server = smtplib.SMTP_SSL(SMTP_SERVER, 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print("✅ 邮件发送成功，含国内可访问链接！")
    except smtplib.SMTPAuthenticationError:
        print("❌ 登录失败：检查QQ邮箱授权码/账号")
    except Exception as e:
        print(f"❌ 邮件发送失败：{e}")

# 核心运行逻辑
if __name__ == "__main__":
    print("🔍 开始抓取彭博资讯...")
    news_list = get_news()
    news_count = len(news_list) if news_list else 0
    make_html(news_list)
    push_to_github()  # 推送文件到GitHub，用于Pages访问
    print("📤 开始发送带链接的邮件...")
    send_email_with_link(news_count)
    print("🎉 流程结束，查收邮箱！")

