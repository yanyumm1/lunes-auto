import os
import time
import platform
from seleniumbase import SB
from pyvirtualdisplay import Display

# ========= 配置 =========
EMAIL = os.getenv("LUNES_EMAIL")
PASSWORD = os.getenv("LUNES_PASSWORD")

LOGIN_URL = "https://dashboard.katabump.com/login"
TARGET_URL = "https://dashboard.katabump.com/servers"

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)


# ========= Xvfb =========
def setup_xvfb():
    if platform.system().lower() == "linux" and not os.environ.get("DISPLAY"):
        display = Display(visible=False, size=(1920, 1080))
        display.start()
        os.environ["DISPLAY"] = display.new_display_var
        print("🖥️ Xvfb 已启动", flush=True)
        return display
    return None


def shot(sb, name):
    path = f"{SCREENSHOT_DIR}/{name}"
    sb.save_screenshot(path)
    print(f"📸 {path}", flush=True)


def get_cookie(sb, name):
    for c in sb.get_cookies():
        if c["name"] == name:
            return c["value"]
    return None


def can_access_target(sb):
    sb.open(TARGET_URL)
    time.sleep(6)
    url = sb.get_current_url()
    print(f"🔎 当前 URL: {url}", flush=True)
    return "/servers" in url and "/login" not in url


# ========= 主逻辑 =========
def main():
    if not EMAIL or not PASSWORD:
        raise RuntimeError("❌ 缺少账号环境变量")

    display = setup_xvfb()

    try:
        with SB(
            uc=True,
            test=True,
            headless=False,
            locale="en",
            incognito=True,
        ) as sb:
            print("🌐 SeleniumBase 浏览器已创建", flush=True)

            # --- 打开登录页 ---
            print("🚀 打开登录页", flush=True)
            sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=6)
            sb.wait_for_element_visible("#email", timeout=30)
            time.sleep(2)
            shot(sb, "01_login_page.png")

            # --- 输入账号密码 ---
            sb.type("#email", EMAIL, timeout=10)
            time.sleep(0.5)
            sb.type("#password", PASSWORD, timeout=10)
            time.sleep(1)

            # --- 尝试触发 Turnstile（不强求） ---
            print("🛡️ 尝试触发 Turnstile", flush=True)
            try:
                sb.uc_gui_click_captcha()
                time.sleep(2)
            except Exception:
                pass

            # --- 提交 ---
            print("🔐 提交登录", flush=True)
            sb.click("button[type='submit']")

            # ⚠️ 给 Cloudflare 行为评分时间（非常重要）
            time.sleep(10)
            shot(sb, "02_after_submit.png")

            # --- 观察 cf_clearance ---
            cf_clearance = get_cookie(sb, "cf_clearance")
            print("🧩 cf_clearance:", bool(cf_clearance), flush=True)

            # --- 最终判定：访问受保护页面 ---
            print("➡️ 验证是否登录成功", flush=True)
            if can_access_target(sb):
                shot(sb, "03_server_page.png")
                print("🎉 登录成功（Cloudflare Managed Mode 放行）", flush=True)
                return

            shot(sb, "04_login_failed.png")
            raise RuntimeError("❌ Cloudflare 未放行（行为评分不足）")

    finally:
        if display:
            display.stop()


if __name__ == "__main__":
    main()