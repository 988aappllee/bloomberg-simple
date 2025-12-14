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
# QQ邮箱信息（已填好你的信息）
SENDER_EMAIL = "1047372945@qq.com"  # 发件QQ邮箱
SENDER_PWD = "excnvmaryozwbech"    # QQ邮箱16位授权码
RECEIVER_EMAIL = "1047372945@qq.com"  # 收件邮箱

# Gitee信息（替换为你的）
GITEE_USER = "988aappllee"    # Gitee主页的用户名（如gitee.com/xxx的xxx）
GITEE_REPO = "bloomberg-gitee"    # 你创建的Gitee仓库名
GITEE_TOKEN = "35e38c0961d0b8bce2a94c1ff2e8b263" # 刚生成的私人令牌
# -------------------------------------------------------------

# Gitee Pages国内可点击链接（自动拼接）
GITEE_PAGE_LINK = f"https://{GITEE_USER}.gitee.io/{GITEE_REPO}/彭博速递.html"

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
            return feedparser.parse(res.text)['entries']
        except Exception as e:
            print(f"⚠️ 第{_+1}次抓取失败：{e}")
            continue
    return []

# 生成带样式的HTML内容
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

# 推送HTML到Gitee仓库（自动同步Pages）
def push_to_gitee():
    try:
        # 克隆Gitee仓库（首次运行）
        gitee_repo_url = f"https://{GITEE_USER}:{GITEE_TOKEN}@gitee.com/{GITEE_USER}/{GITEE_REPO}.git"
        if not os.path.exists(GITEE_REPO):
            subprocess.run(["git", "clone", gitee_repo_url], check=True)
        os.chdir(GITEE_REPO)
        
        # 复制并推送HTML文件
        subprocess.run(["cp", f"../彭博速递.html", "./"], check=True)
        subprocess.run(["git", "config", "--global", "user.name", GITEE_USER], check=True)
        subprocess.run(["git", "config", "--global", "user.email", SENDER_EMAIL], check=True)
        subprocess.run(["git", "add", "彭博速递.html"], check=True)
        subprocess.run(["git", "commit", "-m", f"更新资讯 {datetime.datetime.now().strftime('%Y-%m-%d')}"], check=True)
        subprocess.run(["git", "push", "origin", "master"], check=True)
        os.chdir("..")
        print(f"✅ 已推送到Gitee，链接：{GITEE_PAGE_LINK}")
    except Exception as e:
        print(f"⚠️ 推送Gitee失败（下次重试）：{e}")

# 发送邮件（带可点击链接）
def send_email():
    print("🔍 抓取彭博资讯中...")
    news_list = get_news()
    news_count = len(news_list)
    make_html(news_list)
    push_to_gitee()

    try:
        # 邮件正文：蓝色可点击链接，QQ邮箱直接跳转
        email_html = f"""
        <div style="font-family: 微软雅黑; max-width: 600px; margin: 0 auto;">
            <h3 style="color: #2E4057; margin-bottom: 20px;">彭博速递最新资讯</h3>
            <p style="font-size: 15px; margin-bottom: 25px;">本次共更新 <b style="color: #1E88E5;">{news_count}</b> 条，点击下方链接直接查看：</p>
            <p style="margin-bottom: 30px;">
                <a href="{GITEE_PAGE_LINK}" target="_blank" style="background: #1E88E5; color: #fff; padding: 12px 25px; border-radius: 5px; text-decoration: none; font-weight: bold; font-size: 16px;">
                    🔗 点击打开资讯页面
                </a>
            </p>
            <p style="color: #999; font-size: 12px;">提示：该链接为Gitee国内平台，无需科学上网，手机/电脑均可打开～</p>
        </div>
        """
        msg = MIMEText(email_html, "html", "utf-8")
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"彭博速递（{news_count}条）- 国内点击即开"

        # 发送邮件
        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ 邮件发送成功！{GITEE_PAGE_LINK}")
    except smtplib.SMTPAuthenticationError:
        print("❌ 登录失败：检查QQ邮箱授权码是否正确")
    except Exception as e:
        print(f"❌ 发送失败：{str(e)}")

if __name__ == "__main__":
    send_email()

