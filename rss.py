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

# 生成邮箱可点击的Base64短链接（零注册，避免JSON解析错误）
def make_clickable_link(html_content):
    # 压缩HTML内容后编码，缩短链接长度
    html_bytes = html_content.encode('utf-8')
    base64_str = base64.b64encode(html_bytes).decode('utf-8')
    # 生成QQ邮箱支持的可点击链接（分段处理避免过长）
    link = f"data:text/html;base64,{base64_str[:5000]}..." if len(base64_str) > 5000 else f"data:text/html;base64,{base64_str}"
    return link, base64_str

# 抓取彭博资讯（重试3次）
def get_news():
    for _ in range(3):
        try:
            res = requests.get(
                "https://bloombergnew.buzzing.cc/feed.xml",
                headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"},
                timeout=20,
                verify=False
            )
            res.encoding = 'utf-8'
            entries = feedparser.parse(res.text)['entries']
            return entries[:50]  # 限制条数，避免链接过长
        except Exception as e:
            print(f"⚠️ 抓取失败{_+1}次：{e}")
            continue
    return []

# 生成精简版资讯HTML（减少长度，适配链接）
def make_html(news_list):
    if not news_list:
        return "<h2 style='color: #FFD700; text-align: center;'>暂无彭博资讯</h2>"
    
    html = """
    <!DOCTYPE html>
    <html lang="zh-CN">
    <head>
        <meta charset="utf-8">
        <style>
            body { background: #1a1a1a; color: #fff; font-family: 微软雅黑; max-width: 800px; margin: 20px auto; padding: 20px; }
            h1 { color: #2E4057; text-align: center; margin-bottom: 20px; }
            .item { margin: 15px 0; padding: 10px; border-left: 3px solid #1E88E5; }
            .time { color: #FFD700; font-weight: bold; }
            .link { color: #1E88E5; text-decoration: underline; }
        </style>
    </head>
    <body>
    """
    html += f"<h1>彭博速递（共{len(news_list)}条）</h1>"
    for i, n in enumerate(news_list, 1):
        # 提取时间
        t = re.search(r'(\d{2}:\d{2})<\/time>', n.get("content", [{}])[0].get("value", ""))
        time_str = t.group(1) if t else "未知时间"
        # 简化标题和链接
        title = n.get("title", "")[:80]  # 限制标题长度
        link = n.get("link", "")
        html += f"""
        <div class="item">
            {i}. <span class="time">【{time_str}】</span> {title}
            <br><a href="{link}" class="link" target="_blank">原文链接</a>
        </div>
        """
    html += f"<p style='text-align: right; color: #999;'>更新：{datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</p></body></html>"
    return html

# 发送邮件（适配QQ邮箱的可点击链接）
def send_email():
    print("🔍 抓取彭博资讯中...")
    news_list = get_news()
    news_count = len(news_list)
    html_content = make_html(news_list)
    clickable_link, full_base64 = make_clickable_link(html_content)

    try:
        # 邮件正文：提供可点击链接+完整编码复制提示
        email_html = f"""
        <div style="font-family: 微软雅黑; max-width: 600px; margin: 0 auto;">
            <h3 style="color: #2E4057; margin-bottom: 20px;">彭博速递最新资讯</h3>
            <p style="font-size: 15px; margin-bottom: 20px;">本次共更新 <b style="color: #1E88E5;">{news_count}</b> 条资讯：</p>
            
            <!-- 可点击链接 -->
            <p style="margin-bottom: 30px;">
                <a href="{clickable_link}" target="_blank" style="color: #1E88E5; font-size: 16px; font-weight: bold; text-decoration: underline;">
                    点击打开资讯页面（若无法打开，复制下方完整编码）
                </a>
            </p>
            
            <!-- 完整编码提示 -->
            <div style="background: #f5f5f5; padding: 15px; border-radius: 5px; margin-bottom: 20px;">
                <p style="color: #333; font-size: 12px; margin-bottom: 10px;"><b>完整Base64编码（复制到浏览器地址栏打开）：</b></p>
                <p style="color: #666; font-size: 11px; word-break: break-all;">data:text/html;base64,{full_base64}</p>
            </div>
            
            <p style="color: #999; font-size: 12px;">提示：复制完整编码后，粘贴到浏览器地址栏按回车即可打开～</p>
        </div>
        """
        msg = MIMEText(email_html, "html", "utf-8")
        msg["From"] = SENDER_EMAIL
        msg["To"] = RECEIVER_EMAIL
        msg["Subject"] = f"彭博速递（{news_count}条）- 国内可看"

        # 发送邮件（关闭SSL验证，避免服务器问题）
        server = smtplib.SMTP_SSL("smtp.qq.com", 465, timeout=30)
        server.login(SENDER_EMAIL, SENDER_PWD)
        server.sendmail(SENDER_EMAIL, RECEIVER_EMAIL, msg.as_string())
        server.quit()
        print(f"✅ 邮件发送成功！共{news_count}条资讯")
    except smtplib.SMTPAuthenticationError:
        print("❌ 登录失败：请检查QQ邮箱授权码是否正确（需用16位SMTP授权码，不是登录密码）")
    except Exception as e:
        print(f"❌ 发送失败：{str(e)}")

if __name__ == "__main__":
    send_email()

