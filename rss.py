import feedparser
import smtplib
from email.mime.text import MIMEText
import requests
import re
import datetime
import sys

# 全局编码防乱码
sys.stdout.reconfigure(encoding='utf-8')

# ---------------------- 已填好你的信息 ----------------------
SENDER_EMAIL = "1047372945@qq.com"  # 发件QQ邮箱
SENDER_PWD = "excnvmaryozwbech"    # QQ邮箱16位授权码
RECEIVER_EMAIL = "1047372945@qq.com"  # 收件邮箱
# -----------------------------------------------------------

# 国内无需登录的文本托管（temp.sh，国内可访问、永久保存）
def upload_to_cn_text_host(html_content):
    try:
        # 国内可访问的免费托管（无需登录，自动生成链接）
        url = "https://temp.sh/"
        files = {
            'file': ('彭博速递.html', html_content, 'text/html')
        }
        res = requests.post(url, files=files, timeout=30)
        cn_link = res.text.strip()  # 提取生成的国内链接
        print(f"✅ 国内链接生成成功：{cn_link}")
        return cn_link
    except:
        # 备选国内托管（双重保障，同样无需登录）
        url = "https://paste.c-net.org/"
        data = {
            "content": html_content,
            "format": "html",
            "expire": "never"
        }
        res = requests.post(url, data=data, timeout=30)
        cn_link = res.url
        print(f"✅ 备选国内链接生成成功：{cn_link}")
        return cn_link

# 抓取彭博资讯（重试3次）
def get_news():
    for _ in range(3):
        try:
            res = requests.get("https://bloombergnew.buzzing.cc/feed.xml", headers={"User-Agent": "Mozilla/5.0"}, timeout=20)
            res.encoding = 'utf-8'
            return feedparser.parse(res.text)['entries']
        except:
            continue
    return []

# 生成带样式的HTML内容（黄色时间+蓝色链接）
def make_html(news_list):
    if not news_list:
        return "<h2 style='color: #FFD700;'>暂无彭博资讯（资讯源暂时不可用）</h2>"
    
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
        <h1>彭博速递（共{len(news_list)}条最新资讯）</h1>
    """
    for i, n in enumerate(news_list, 1):
        # 提取时间
        t = re.search(r'(\d{2}:\d{2})<\/time>', n.get("content", [{}])[0].get("value", ""))
        time_str = t.group(1) if t else "未知时间"
        # 编码容错
        title = n.get("title", "").encode('utf-8', errors='replace').decode('utf-8')
        link = n.get("link", "").encode('utf-8', errors='replace').decode('utf-8')
        # 拼接单条资讯
        html += f"""
        <div class="item">
            {i}. <span class="time">【{time_str}】</span> {title}
            <br><a href="{link}" class="link">👉 原文链接</a>
        </div>
        """
    html += f"<p style='text-align: right; color: #999;'>更新时间：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p></body></html>"
    return html

# 发送邮件（带国内托管链接，QQ不屏蔽）
def send_email():
    print("🔍 抓取彭博资讯中...")
    news_list = get_news()
    news_count = len(news_list)
    html_content = make_html(news_list)
    
    print("📤 上传内容到国内托管平台...")
    cn_link = upload_to_cn_text_host(html_content)
    
    try:
        # 纯文本邮件（QQ邮箱绝对不屏蔽）
        email_content = f"""
彭博速递最新资讯更新啦！本次共推送{news_count}条，国内直接打开链接：

{cn_link}

提示：
1. 链接是国内托管平台，不用科学上网，复制到浏览器秒开；
2. 打开后能看到黄色时间、蓝色可点击的资讯链接；
3. 链接永久有效，无需下载任何文件、无需登录～
        """
        msg = MIMEText(email_content, "plain", "utf-8")
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"彭博速递最新资讯（{news_count}条）- 国内可访问"

        # 发送邮件
        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ 邮件发送成功！国内链接：{cn_link}")
    except smtplib.SMTPAuthenticationError:
        print("❌ 登录失败：检查QQ邮箱授权码/账号是否正确")
    except Exception as e:
        print(f"❌ 邮件发送失败：{str(e)}")

# 一键运行（不用管其他，点运行就行）
if __name__ == "__main__":
    send_email()

