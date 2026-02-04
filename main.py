import os
import time
import platform
from seleniumbase import SB
from pyvirtualdisplay import Display

# ====== 配置 ======
LOGIN_URL = "https://betadash.lunes.host/login?next=/"
TARGET_URL = "https://betadash.lunes.host/servers/63531"

EMAIL = os.getenv("LUNES_EMAIL")
PASSWORD = os.getenv("LUNES_PASSWORD")

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


def start_xvfb():
    if platform.system().lower() == "linux" and not os.environ.get("DISPLAY"):
        display = Display(visible=False, size=(1920, 1080))
        display.start()
        print("🖥️ Xvfb started")
        return display
    return None


def shot(sb, name):
    path = f"{SCREENSHOT_DIR}/{name}"
    sb.save_screenshot(path)
    print(f"📸 {path}")


def main():
    if not EMAIL or not PASSWORD:
        raise RuntimeError("❌ 缺少 LUNES_EMAIL / LUNES_PASSWORD")

    display = start_xvfb()

    try:
        with SB(
            uc=True,
            locale="en",
            headless=False,     # ❗ CI 下也保持 headful（Xvfb）
            test=True
        ) as sb:

            print("🚀 打开登录页")
            sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=6)
            sb.wait_for_element_visible("input[type='email']", timeout=30)

            shot(sb, "01_login_page.png")

            # ===== 输入账号 =====
            sb.click("input[type='email']")
            sb.type("input[type='email']", EMAIL, delay=60)

            sb.click("input[type='password']")
            sb.type("input[type='password']", PASSWORD, delay=60)

            time.sleep(1)

            sb.click("button[type='submit']")
            print("🔐 已提交登录")

            # ===== 等登录完成 =====
            sb.wait_for_element_visible("body", timeout=30)
            time.sleep(3)

            shot(sb, "02_after_login.png")

            # ===== 访问服务器页 =====
            print("➡️ 打开服务器页面")
            sb.uc_open_with_reconnect(TARGET_URL, reconnect_time=6)
            sb.wait_for_element_visible("body", timeout=30)
            time.sleep(3)

            shot(sb, "03_server_page.png")

            # ===== 简单成功判断 =====
            url = sb.get_current_url()
            title = sb.get_title()

            print("📍 URL:", url)
            print("📄 Title:", title)

            if "/servers/" in url:
                print("✅ 登录并访问成功")
            else:
                raise RuntimeError("❌ 未成功进入服务器页面")

    finally:
        if display:
            display.stop()


if __name__ == "__main__":
    main()