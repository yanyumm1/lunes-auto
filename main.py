import os
import time
import platform
from seleniumbase import SB
from pyvirtualdisplay import Display

LOGIN_URL = "https://betadash.lunes.host/login?next=/"
TARGET_URL = "https://betadash.lunes.host/servers/63531"

EMAIL = os.getenv("LUNES_EMAIL")
PASSWORD = os.getenv("LUNES_PASSWORD")

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def setup_xvfb():
    """
    启动 Xvfb（虚拟显示）并修复 python-xlib 解析错误
    """
    if platform.system().lower() == "linux" and not os.environ.get("DISPLAY"):
        display = Display(visible=False, size=(1920, 1080), use_xauth=False)
        display.start()
        os.environ["DISPLAY"] = display.new_display_var
        print("🖥️ Xvfb 已启动")
        return display
    return None


def shot(sb, name):
    path = f"{SCREENSHOT_DIR}/{name}"
    sb.save_screenshot(path)
    print(f"📸 {path}")


def get_cookie(sb, name):
    for c in sb.get_cookies():
        if c.get("name") == name:
            return c.get("value")
    return None


def is_logged_in(sb):
    url = sb.get_current_url()
    if "/login" in url:
        return False
    if sb.is_element_present("input[type='email']"):
        return False
    return True


def main():
    if not EMAIL or not PASSWORD:
        raise RuntimeError("❌ 缺少账号环境变量")

    display = setup_xvfb()

    try:
        with SB(uc=True, test=True, headless=False) as sb:  # ⚠️ 非 headless
            print("🚀 打开登录页")
            sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=6)
            sb.wait_for_element_visible("input[type='email']", timeout=30)
            shot(sb, "01_login_page.png")

            sb.type("input[type='email']", EMAIL)
            sb.type("input[type='password']", PASSWORD)

            # 触发 Turnstile（Managed / Invisible，不看 token）
            print("🛡️ 触发 Cloudflare Turnstile")
            try:
                sb.uc_gui_click_captcha()
            except Exception as e:
                print("⚠️ Turnstile 交互异常:", e)

            time.sleep(2)
            sb.click("button[type='submit']")
            time.sleep(5)
            shot(sb, "02_after_login.png")

            cf_clearance = get_cookie(sb, "cf_clearance")
            print("🧩 cf_clearance:", bool(cf_clearance))

            if not is_logged_in(sb):
                shot(sb, "02_login_failed.png")
                raise RuntimeError("❌ 登录失败（后端未建 session）")

            print("✅ 登录成功")

            print("➡️ 打开服务器页")
            sb.open(TARGET_URL)
            sb.wait_for_element_visible("body", timeout=30)
            time.sleep(3)
            shot(sb, "03_server_page.png")

            if "/servers/" not in sb.get_current_url():
                raise RuntimeError("❌ 服务器页访问失败")

            print("🎉 登录 + 页面访问全部成功")

    finally:
        if display:
            display.stop()