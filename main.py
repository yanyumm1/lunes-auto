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


def slow_type(sb, selector, text, delay=0.06):
    sb.click(selector)
    sb.clear(selector)
    for ch in text:
        sb.send_keys(selector, ch)
        time.sleep(delay)


def get_cookie(sb, name):
    for c in sb.get_cookies():
        if c.get("name") == name:
            return c.get("value")
    return None


def wait_for_turnstile_token(sb, timeout=20):
    """等待 cf-turnstile-response 被写入"""
    print("⏳ 等待 Turnstile token 生成")
    for i in range(timeout):
        try:
            val = sb.get_attribute(
                "input[name='cf-turnstile-response']",
                "value"
            )
            if val and len(val) > 20:
                print("✅ Turnstile token 已生成")
                return val
        except Exception:
            pass
        time.sleep(1)

    return None


def is_logged_in(sb):
    """判断是否真的登录"""
    url = sb.get_current_url()
    if "/login" in url:
        return False

    # 登录后一般不会再看到 email 输入框
    if sb.is_element_present("input[type='email']"):
        return False

    return True


def main():
    if not EMAIL or not PASSWORD:
        raise RuntimeError("❌ 缺少 LUNES_EMAIL / LUNES_PASSWORD")

    with SB(uc=True, headless=True, test=True) as sb:

        print("🚀 打开登录页")
        sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=6)
        sb.wait_for_element_visible("input[type='email']", timeout=30)

        shot(sb, "01_login_page.png")

        slow_type(sb, "input[type='email']", EMAIL)
        slow_type(sb, "input[type='password']", PASSWORD)

        # ==== 触发 Turnstile ====
        print("🛡️ 触发 Cloudflare Turnstile")
        try:
            sb.uc_gui_click_captcha()
        except Exception as e:
            print("⚠️ Turnstile 点击异常:", e)

        # ==== 等 token ====
        token = wait_for_turnstile_token(sb)
        cf_clearance = get_cookie(sb, "cf_clearance")

        print("🧩 cf_clearance:", bool(cf_clearance))
        print("🧪 turnstile token:", bool(token))

        shot(sb, "03_cf_state.png")

        if not token:
            raise RuntimeError("❌ Turnstile token 未生成，无法登录")

        # ==== 提交登录 ====
        print("🔐 提交登录")
        sb.click("button[type='submit']")
        time.sleep(5)

        shot(sb, "04_after_login.png")

        if not is_logged_in(sb):
            shot(sb, "04_login_failed.png")
            raise RuntimeError("❌ 登录失败（后端未接受 Turnstile）")

        print("✅ 登录成功")

        # ==== 打开服务器页 ====
        sb.open(TARGET_URL)
        sb.wait_for_element_visible("body", timeout=30)
        time.sleep(3)

        shot(sb, "05_server_page.png")

        if "/servers/" not in sb.get_current_url():
            raise RuntimeError("❌ 无法访问服务器页面")

        print("🎉 已成功登录并访问服务器页")


if __name__ == "__main__":
    main()