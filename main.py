import os
import time
from seleniumbase import SB

LOGIN_URL = "https://betadash.lunes.host/login?next=/"
TARGET_URL = "https://betadash.lunes.host/servers/63531"

EMAIL = os.getenv("LUNES_EMAIL")
PASSWORD = os.getenv("LUNES_PASSWORD")

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def shot(sb, name):
    path = f"{SCREENSHOT_DIR}/{name}"
    sb.save_screenshot(path)
    print(f"📸 {path}")


def get_cf_clearance(sb):
    for c in sb.get_cookies():
        if c.get("name") == "cf_clearance":
            return c.get("value")
    return None


def slow_type(sb, selector, text, delay=0.06):
    """模拟真人逐字输入"""
    sb.click(selector)
    sb.clear(selector)
    for ch in text:
        sb.send_keys(selector, ch)
        time.sleep(delay)


def main():
    if not EMAIL or not PASSWORD:
        raise RuntimeError("❌ 缺少 LUNES_EMAIL / LUNES_PASSWORD")

    with SB(
        uc=True,
        test=True,
        headless=True,   # ✅ GitHub Actions 必须 headless
    ) as sb:

        print("🚀 打开登录页")
        sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=6)
        sb.wait_for_element_visible("input[type='email']", timeout=30)

        shot(sb, "01_login_page.png")

        # ===== 输入账号密码（慢速，像真人）=====
        print("⌨️ 输入账号")
        slow_type(sb, "input[type='email']", EMAIL)

        print("⌨️ 输入密码")
        slow_type(sb, "input[type='password']", PASSWORD)

        time.sleep(1)

        # ===== Cloudflare Turnstile =====
        print("🛡️ 处理 Cloudflare Turnstile")

        cf_clearance = None
        for i in range(1, 4):
            print(f"🧠 尝试 CF 勾选 {i}/3")
            try:
                sb.uc_gui_click_captcha()
            except Exception as e:
                print("⚠️ CF 点击异常:", e)

            time.sleep(4)
            cf_clearance = get_cf_clearance(sb)
            print("🧩 cf_clearance:", cf_clearance)

            if cf_clearance:
                print("✅ Cloudflare 已通过")
                break

        if not cf_clearance:
            shot(sb, "02_cf_failed.png")
            raise RuntimeError("❌ Cloudflare 未通过，终止")

        shot(sb, "03_cf_passed.png")

        # ===== 提交登录 =====
        print("🔐 提交登录")
        sb.click("button[type='submit']")
        sb.wait_for_element_visible("body", timeout=30)
        time.sleep(3)

        shot(sb, "04_after_login.png")

        # ===== 打开服务器页 =====
        print("➡️ 打开服务器页面")
        sb.uc_open_with_reconnect(TARGET_URL, reconnect_time=6)
        sb.wait_for_element_visible("body", timeout=30)
        time.sleep(3)

        shot(sb, "05_server_page.png")

        if "/servers/" not in sb.get_current_url():
            raise RuntimeError("❌ 未成功进入服务器页面")

        print("🎉 登录成功 + 页面访问成功")


if __name__ == "__main__":
    main()