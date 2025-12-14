import feedparser
import smtplib
from email.mime.text import MIMEText
import requests
import re
import datetime
import sys
import subprocess
import os

# 全局编码防乱码
sys.stdout.reconfigure(encoding='utf-8')

# ---------------------- 配置信息（必改！）----------------------
# QQ邮箱信息（已填好）
SENDER_EMAIL = "1047372945@qq.com"
SENDER_PWD = "excnvmaryozwbech"
RECEIVER_EMAIL = "1047372945@qq.com"

# GitHub信息（替换为你的）
GITHUB_USER = "988aappllee"  # 如github.com/xxx的xxx
GITHUB_REPO = "bloomberg-simple" # 你的GitHub仓库名
# -------------------------------------------------------------

# 生成国内反代链接（gh-proxy.com，零实名认证，国内可访问）
def get_cn_proxy_link():
    # GitHub Pages原链接
    github_pages_link = f"https://{GITHUB_USER}.github.io/{GITHUB_REPO}/彭博速递.html"
    # 国内反代链接（gh-proxy.com，点击即开）
    cn_proxy_link = f"https://gh-proxy.com/{github_pages_link}"
    print(f"✅ 国内反代链接生成：{cn_proxy_link}")
    return cn_proxy_link

# 抓取彭博资讯（重试3次）
def get_news():
    for _ in range(3):
        try:
            res = requests.get(
                "https://bloombergnew.buzzing.cc/feed.xml",
                headers={"User-Agent": "Mozilla/5.0"},
                timeout=20
            )
            res.encoding = 'utf-8'
            return feedparser.parse(res.text)['entries'][:50]  # 限制条数，加快加载
        except Exception as e:
            print(f"⚠️ 抓取失败{_+1}次：{e}")
            continue
    return []

# 生成带样式的HTML
def make_html(news_list):
    if not news_list:
        html = "<h2 style='color: #FFD700; text-align: center;'>暂无彭博资讯</h2>"
    else:
        html = f"""
        <!DOCTYPE html>
        <html lang="zh-CN">
        <head>
            <meta charset="utf-8">
            <style>
                body {{ background: #1a1a1a; color: #fff; font-family: 微软雅黑; max-width: 800px; margin: 20px auto; padding: 20px; }}
                h1 {{ color: #2E4057; text-align: center; margin-bottom: 30px; }}
                .item {{ margin: 20px 0; padding: 15px; border-left: 4px solid #1E88E5; background: #222; border-radius: 4px; }}
                .time {{ color: #FFD700; font-weight: bold; margin-right: 10px; }}
                .link {{ color: #1E88E5; text-decoration: underline; margin-top: 5px; display: inline-block; }}
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
                <span class="time">【{time_str}】</span>
                <span>{title}</span>
                <br>
                <a href="{link}" class="link" target="_blank">👉 查看原文</a>
            </div>
            """
        html += f"<p style='text-align: right; color: #999;'>更新：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p></body></html>"
    
    # 保存HTML文件
    with open("彭博速递.html", 'w', encoding='utf-8') as f:
        f.write(html)
    print("✅ HTML文件生成成功")
    return html

# 推送HTML到GitHub（同步Pages）
def push_to_github():
    try:
        # 配置Git用户信息
        subprocess.run(["git", "config", "--global", "user.name", GITHUB_USER], check=True)
        subprocess.run(["git", "config", "--global", "user.email", SENDER_EMAIL], check=True)
        # 提交并推送
        subprocess.run(["git", "add", "彭博速递.html"], check=True)
        subprocess.run(["git", "commit", "-m", f"更新资讯 {datetime.datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("✅ 已推送到GitHub，Pages自动同步")
    except Exception as e:
        print(f"⚠️ 推送GitHub失败（下次重试）：{e}")

# 发送带可点击反代链接的邮件
def send_email():
    print("🔍 抓取彭博资讯中...")
    news_list = get_news()
    news_count = len(news_list)
    make_html(news_list)
    push_to_github()
    cn_link = get_cn_proxy_link()

    try:
        # 邮件正文：蓝色可点击反代链接，QQ邮箱直接跳转
        email_html = f"""
        <div style="font-family: 微软雅黑; max-width: 600px; margin: 0 auto;">
            <h3 style="color: #2E4057; margin-bottom: 20px;">彭博速递最新资讯</h3>
            <p style="font-size: 15px; margin-bottom: 25px;">本次共更新 <b style="color: #1E88E5;">{news_count}</b> 条，点击下方链接直接查看：</p>
            <p style="margin-bottom: 30px;">
                <a href="{cn_link}" target="_blank" style="background: #1E88E5; color: #fff; padding: 12px 25px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 16px;">
                    🔗 点击打开资讯页面（国内秒开）
                </a>
            </p>
            <p style="color: #999; font-size: 12px;">提示：该链接为国内反代平台，无需实名认证、无需科学上网，手机/电脑均可打开～</p>
        </div>
        """
        msg = MIMEText(email_html, "html", "utf-8")
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"彭博速递（{news_count}条）- 国内点击即开"

        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ 邮件发送成功！链接：{cn_link}")
    except smtplib.SMTPAuthenticationError:
        print("❌ 登录失败：检查QQ邮箱授权码是否正确")
    except Exception as e:
        print(f"❌ 发送失败：{e}")

if __name__ == "__main__":
    send_email()

