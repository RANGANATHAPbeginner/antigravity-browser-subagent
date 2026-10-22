"""Antigravity Dedicated Browser Agent - Core Automation Engine
Connects to the dedicated interactive Google Chrome window via Chrome DevTools Protocol (CDP).
Supports genuine graceful shutdown via native Browser.close, 1-shot routing, 100% tool parity with Antigravity IDE.
"""

import sys
import os
import json
import time
import shutil
import subprocess
import urllib.request
import asyncio
from pathlib import Path

CDP_PORT = 9222
CDP_URL = f"http://127.0.0.1:{CDP_PORT}"
PROFILE_DIR = Path(r"C:\Users\super\.gemini\browser-agent-profile")
BACKUPS_DIR = Path(r"C:\Users\super\.gemini\browser-agent-backups")
TARGET_URL_FILE = PROFILE_DIR / "target_url.txt"
LAUNCHER_CMD = Path(r"D:\Tools\browser-agent\launcher.cmd")

def is_cdp_available(timeout: float = 1.0) -> bool:
    try:
        req = urllib.request.urlopen(f"{CDP_URL}/json/version", timeout=timeout)
        data = json.loads(req.read().decode("utf-8"))
        return "Browser" in data
    except Exception:
        return False

def list_tabs():
    try:
        req = urllib.request.urlopen(f"{CDP_URL}/json/list", timeout=2.0)
        return json.loads(req.read().decode("utf-8"))
    except Exception:
        return []

def _normalize_url(url: str) -> str:
    if not url or url.strip() == "":
        return "chrome://newtab"
    url = url.strip()
    if url.startswith("http://") or url.startswith("https://") or url.startswith("chrome://") or url.startswith("about:"):
        return url
    return f"https://{url}"

def open_tab_cdp(url: str = "chrome://newtab") -> dict:
    target = _normalize_url(url)
    req = urllib.request.Request(f"{CDP_URL}/json/new?{target}", method="PUT")
    with urllib.request.urlopen(req, timeout=3.0) as resp:
        return json.loads(resp.read().decode("utf-8"))

def activate_tab_cdp(tab_id: str) -> bool:
    try:
        req = urllib.request.Request(f"{CDP_URL}/json/activate/{tab_id}", method="POST")
        with urllib.request.urlopen(req, timeout=2.0):
            return True
    except Exception:
        return False

def close_tab_cdp(tab_id: str) -> bool:
    try:
        req = urllib.request.Request(f"{CDP_URL}/json/close/{tab_id}", method="POST")
        with urllib.request.urlopen(req, timeout=2.0):
            return True
    except Exception:
        return False

def launch_browser(url: str = None, wait_sec: int = 10) -> bool:
    target = _normalize_url(url)

    if is_cdp_available():
        if target != "chrome://newtab":
            print(f"[BrowserAgent] Browser online. 1-Shot opening: {target}")
            tab = open_tab_cdp(target)
            activate_tab_cdp(tab.get("id", ""))
        else:
            print("[BrowserAgent] Browser already running with active session.")
        return True

    PROFILE_DIR.mkdir(parents=True, exist_ok=True)
    TARGET_URL_FILE.write_text(target, encoding="utf-8")

    # Spawning interactive browser via Windows Task Scheduler
    res = subprocess.run(["schtasks", "/Run", "/TN", "AntigravityAgentBrowser"], capture_output=True, text=True)
    if res.returncode != 0:
        shortcut = Path(r"C:\Users\super\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Antigravity Browser Agent.lnk")
        if shortcut.exists():
            subprocess.Popen(["explorer.exe", str(shortcut)])
        else:
            subprocess.Popen(["cmd.exe", "/c", str(LAUNCHER_CMD)])

    start_time = time.time()
    while time.time() - start_time < wait_sec:
        if is_cdp_available():
            print(f"[BrowserAgent] Launched directly to {target} in {time.time() - start_time:.2f}s.")
            return True
        time.sleep(0.5)
    return False

def close_browser(timeout_sec: float = 5.0) -> bool:
    """Proper graceful shutdown: sends native Browser.close to the browser CDP target so Chrome flushes state and exits naturally."""
    if is_cdp_available():
        try:
            from playwright.async_api import async_playwright
            async def do_close():
                async with async_playwright() as p:
                    browser = await p.chromium.connect_over_cdp(CDP_URL)
                    cdp = await browser.new_browser_cdp_session()
                    await cdp.send("Browser.close")
            asyncio.run(do_close())

            # Wait for Chrome to cleanly exit
            t0 = time.time()
            while time.time() - t0 < timeout_sec:
                if not is_cdp_available():
                    print("[BrowserAgent] Chrome shut down gracefully and cleanly.")
                    return True
                time.sleep(0.3)
        except Exception:
            pass

    # Safety fallback only if process hung
    ps_cmd = 'Get-CimInstance Win32_Process -Filter "Name = \'chrome.exe\'" | Where-Object { $_.CommandLine -like "*browser-agent-profile*" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }'
    subprocess.run(["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd], capture_output=True, text=True)
    print("[BrowserAgent] Browser processes stopped.")
    return True

def kill_browser() -> bool:
    return close_browser()

async def _playwright_action(action_fn):
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        browser = await p.chromium.connect_over_cdp(CDP_URL)
        context = browser.contexts[0] if browser.contexts else await browser.new_context()
        try:
            return await action_fn(browser, context)
        finally:
            await browser.close()

def run_action(action_fn):
    if not is_cdp_available():
        launch_browser()
    return asyncio.run(_playwright_action(action_fn))

def _get_active_page(context):
    pages = [p for p in context.pages if not p.url.startswith("devtools://") and not p.url.startswith("chrome-extension://") and not p.url.startswith("chrome://omnibox")]
    return pages[-1] if pages else None

# --- Core Tools (100% Parity with Antigravity IDE) ---

def navigate(url: str):
    target = _normalize_url(url)
    async def fn(browser, context):
        page = _get_active_page(context) or await context.new_page()
        try:
            await page.goto(target, wait_until="commit", timeout=10000)
        except Exception:
            pass
        return {"title": await page.title(), "url": page.url}
    return run_action(fn)

def screenshot(output_path: str, full_page: bool = False):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return None
        out_p = Path(output_path).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        await page.screenshot(path=str(out_p), full_page=full_page)
        return str(out_p)
    return run_action(fn)

def click(selector: str):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return False
        await page.click(selector, timeout=5000)
        return True
    return run_action(fn)

def click_coords(x: int, y: int):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return False
        await page.mouse.click(x, y)
        return True
    return run_action(fn)

def type_text(selector: str, text: str):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return False
        await page.fill(selector, text, timeout=5000)
        return True
    return run_action(fn)

def press_key(key: str):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return False
        await page.keyboard.press(key)
        return True
    return run_action(fn)

def scroll(delta_x: int = 0, delta_y: int = 400):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return False
        await page.mouse.wheel(delta_x, delta_y)
        return True
    return run_action(fn)

def hover(selector: str):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return False
        await page.hover(selector, timeout=5000)
        return True
    return run_action(fn)

def wait_for(selector: str, timeout: int = 10000):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return False
        await page.wait_for_selector(selector, timeout=timeout)
        return True
    return run_action(fn)

def eval_js(script: str):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return None
        return await page.evaluate(script)
    return run_action(fn)

def get_dom(selector: str = "body"):
    async def fn(browser, context):
        page = _get_active_page(context)
        if not page:
            return ""
        if selector == "body":
            return await page.evaluate("() => document.body.innerText")
        el = await page.query_selector(selector)
        return await el.inner_text() if el else ""
    return run_action(fn)

# --- Profile Persistence & Malleability ---

def export_auth(output_json: str = "auth_state.json"):
    async def fn(browser, context):
        out_p = Path(output_json).resolve()
        out_p.parent.mkdir(parents=True, exist_ok=True)
        await context.storage_state(path=str(out_p))
        return str(out_p)
    return run_action(fn)

def clear_cache():
    async def fn(browser, context):
        page = _get_active_page(context)
        if page:
            cdp = await context.new_cdp_session(page)
            await cdp.send("Network.clearBrowserCache")
            return True
        return False
    return run_action(fn)

def clear_cookies():
    async def fn(browser, context):
        await context.clear_cookies()
        return True
    return run_action(fn)

def reset_profile():
    close_browser()
    time.sleep(1.5)
    if PROFILE_DIR.exists():
        for item in PROFILE_DIR.iterdir():
            try:
                if item.is_dir():
                    shutil.rmtree(item, ignore_errors=True)
                else:
                    item.unlink(missing_ok=True)
            except Exception:
                pass
    return True

def backup_profile(name: str = "default_backup"):
    BACKUPS_DIR.mkdir(parents=True, exist_ok=True)
    dest = BACKUPS_DIR / name
    if dest.exists():
        shutil.rmtree(dest, ignore_errors=True)
    dest.mkdir(parents=True, exist_ok=True)

    cmd = [
        "robocopy", str(PROFILE_DIR), str(dest),
        "/E", "/XD", "Cache", "Code Cache", "*ShaderCache", "Dawn*Cache", "Crashpad",
        "/XF", "*.lock", "lockfile", "Singleton*",
        "/R:0", "/W:0", "/NFL", "/NDL", "/NJH", "/NJS"
    ]
    subprocess.run(cmd, shell=True)
    return str(dest)

def restore_profile(name: str = "default_backup"):
    src = BACKUPS_DIR / name
    if not src.exists():
        raise FileNotFoundError(f"Backup '{name}' does not exist in {BACKUPS_DIR}")
    close_browser()
    time.sleep(1.5)
    reset_profile()
    cmd = [
        "robocopy", str(src), str(PROFILE_DIR),
        "/E", "/R:0", "/W:0", "/NFL", "/NDL", "/NJH", "/NJS"
    ]
    subprocess.run(cmd, shell=True)
    return True
