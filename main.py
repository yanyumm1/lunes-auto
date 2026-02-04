import os
import time
import platform
import sys
from seleniumbase import SB
from pyvirtualdisplay import Display

# --------------------------
# 环境变量
# --------------------------
LOGIN_URL = "https://betadash.lunes.host/login?next=/"
TARGET_URL = "https://betadash.lunes.host/servers/63531"

EMAIL = os.getenv("LUNES_EMAIL")
PASSWORD = os.getenv("LUNES_PASSWORD")

SCREENSHOT_DIR = "screenshots"
os.makedirs(SCREENSHOT_DIR, exist_ok=True)

# --------------------------
# 设置 stdout 实时输出
# --------------------------
sys.stdout.reconfigure(line_buffering=True)

# --------------------------
# Xvfb 初始化
# --------------------------
def setup_xvfb():
    if platform.system().lower() == "linux" and not os.environ.get("DISPLAY"):
        display = Display(visible=False, size=(1920, 1080), use_xauth=False)
        display.start()
        os.environ["DISPLAY"] = display.new_display_var
        print("🖥️ Xvfb 已启动", flush=True)
        return display
    return None

# --------------------------
# 截图函数
# --------------------------
def shot(sb, name):
    path = f"{SCREENSHOT_DIR}/{name}"
    sb.save_screenshot(path)
    print(f"📸 {path}", flush=True)

# --------------------------
# 获取 cookie
# --------------------------
def get_cookie(sb, name):
    for c in sb.get_cookies():
        if c.get("name") == name:
            return c.get("value")
    return None

# --------------------------
# 判断是否登录成功
# --------------------------
def is_logged_in(sb):
    url = sb.get_current_url()
    if "/login" in url:
        return False
    if sb.is_element_present("input[type='email']"):
        return False
    return True

# --------------------------
# 主流程
# --------------------------
def main():
    if not EMAIL or not PASSWORD:
        raise RuntimeError("❌ 缺少账号环境变量")

    display = setup_xvfb()

    try:
        # ✅ demo_mode=True 会打印每一步操作
        with SB(uc=True, test=True, headless=False, demo_mode=True) as sb:
            print("🌐 SeleniumBase 浏览器已创建", flush=True)

            print("🚀 打开登录页", flush=True)
            sb.uc_open_with_reconnect(LOGIN_URL, reconnect_time=6)
            sb.wait_for_element_visible("input[type='email']", timeout=30)
            shot(sb, "01_login_page.png")

            sb.type("input[type='email']", EMAIL)
            sb.type("input[type='password']", PASSWORD)

            # 触发 Turnstile（Managed / Invisible，不依赖 DOM token）
            print("🛡️ 触发 Cloudflare Turnstile", flush=True)
            try:
                sb.uc_gui_click_captcha()
            except Exception as e:
                print(f"⚠️ Turnstile 交互异常: {e}", flush=True)

            time.sleep(2)
            print("🔐 提交登录", flush=True)
            sb.click("button[type='submit']")
            time.sleep(5)
            shot(sb, "02_after_login.png")

            cf_clearance = get_cookie(sb, "cf_clearance")
            print("🧩 cf_clearance:", bool(cf_clearance), flush=True)

            if not is_logged_in(sb):
                shot(sb, "02_login_failed.png")
                raise RuntimeError("❌ 登录失败（后端未建 session）")

            print("✅ 登录成功", flush=True)

            print("➡️ 打开服务器页", flush=True)
            sb.open(TARGET_URL)
            sb.wait_for_element_visible("body", timeout=30)
            time.sleep(3)
            shot(sb, "03_server_page.png")

            if "/servers/" not in sb.get_current_url():
                raise RuntimeError("❌ 服务器页访问失败")

            print("🎉 登录 + 页面访问全部成功", flush=True)

    finally:
        if display:
            display.stop()

if __name__ == "__main__":
    main()