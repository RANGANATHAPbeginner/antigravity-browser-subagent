#!/usr/bin/env python3
"""Antigravity Browser Agent CLI
Universal CLI to manage and automate the dedicated interactive browser window.
Provides graceful shutdown, 1-shot direct destination routing, 100% tool parity with Antigravity IDE.
"""

import sys
import os
import json
import argparse
from pathlib import Path

# Add tool directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import agent

def main():
    parser = argparse.ArgumentParser(description="Antigravity Dedicated Browser Agent CLI")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # launch
    p_launch = subparsers.add_parser("launch", help="Launch dedicated browser window (clean new tab by default)")
    p_launch.add_argument("url", nargs="?", default=None, help="Optional direct destination URL")

    # status
    subparsers.add_parser("status", help="Check status of browser and CDP endpoint")

    # tabs
    subparsers.add_parser("tabs", help="List all open browser tabs")

    # goto
    p_goto = subparsers.add_parser("goto", help="Navigate active page to URL")
    p_goto.add_argument("url", help="URL to navigate to")

    # screenshot
    p_shot = subparsers.add_parser("screenshot", help="Capture screenshot of active page")
    p_shot.add_argument("output", nargs="?", default="browser_screenshot.png", help="Output file path")
    p_shot.add_argument("--full", action="store_true", help="Capture full page screenshot")

    # click
    p_click = subparsers.add_parser("click", help="Click an element by CSS or XPath selector")
    p_click.add_argument("selector", help="Element selector")

    # click-pixel
    p_pixel = subparsers.add_parser("click-pixel", help="Click coordinates (x, y)")
    p_pixel.add_argument("x", type=int, help="X coordinate")
    p_pixel.add_argument("y", type=int, help="Y coordinate")

    # type
    p_type = subparsers.add_parser("type", help="Type text into an input element")
    p_type.add_argument("selector", help="Element selector")
    p_type.add_argument("text", help="Text to type")

    # press
    p_press = subparsers.add_parser("press", help="Press a keyboard key (Enter, Escape, Tab, etc.)")
    p_press.add_argument("key", help="Key name")

    # scroll
    p_scroll = subparsers.add_parser("scroll", help="Scroll the page vertically or horizontally")
    p_scroll.add_argument("delta_y", nargs="?", type=int, default=400, help="Vertical scroll amount")
    p_scroll.add_argument("delta_x", nargs="?", type=int, default=0, help="Horizontal scroll amount")

    # hover
    p_hover = subparsers.add_parser("hover", help="Hover over an element")
    p_hover.add_argument("selector", help="Element selector")

    # wait
    p_wait = subparsers.add_parser("wait", help="Wait for an element to appear")
    p_wait.add_argument("selector", help="Element selector")
    p_wait.add_argument("--timeout", type=int, default=10000, help="Timeout in milliseconds")

    # dom
    p_dom = subparsers.add_parser("dom", help="Get inner text or DOM content")
    p_dom.add_argument("selector", nargs="?", default="body", help="Element selector")

    # eval
    p_eval = subparsers.add_parser("eval", help="Evaluate JavaScript on the active page")
    p_eval.add_argument("script", help="JavaScript code snippet")

    # export-auth
    p_exp = subparsers.add_parser("export-auth", help="Export cookies and storage state to JSON")
    p_exp.add_argument("output", nargs="?", default="auth_state.json", help="Output JSON path")

    # clear-cache
    subparsers.add_parser("clear-cache", help="Clear HTTP caches without logging out")

    # clear-cookies
    subparsers.add_parser("clear-cookies", help="Clear session cookies & log out without wiping browser settings")

    # reset
    subparsers.add_parser("reset", help="Wipe all cookies, cache, and session for a fresh sandbox")

    # backup
    p_backup = subparsers.add_parser("backup", help="Snapshot the current profile session")
    p_backup.add_argument("name", nargs="?", default="default_backup", help="Snapshot name")

    # restore
    p_restore = subparsers.add_parser("restore", help="Restore a saved profile session snapshot")
    p_restore.add_argument("name", nargs="?", default="default_backup", help="Snapshot name")

    # close / kill
    subparsers.add_parser("close", help="Gracefully shut down dedicated browser instance")
    subparsers.add_parser("kill", help="Gracefully shut down dedicated browser instance")

    args = parser.parse_args()

    if not args.command or args.command == "status":
        online = agent.is_cdp_available()
        tabs = agent.list_tabs() if online else []
        print(f"Browser Agent Status: {'ONLINE' if online else 'OFFLINE'}")
        print(f"CDP Port: {agent.CDP_PORT}")
        print(f"Profile: {agent.PROFILE_DIR}")
        print(f"Active Tabs: {len(tabs)}")
        for t in tabs:
            if not t.get("url", "").startswith("chrome://"):
                print(f"  - [{t.get('title')}] {t.get('url')}")
        return

    if args.command == "launch":
        success = agent.launch_browser(args.url)
        print(f"Launch {'SUCCESS' if success else 'FAILED'}")

    elif args.command == "tabs":
        tabs = agent.list_tabs()
        print(json.dumps(tabs, indent=2))

    elif args.command == "goto":
        res = agent.navigate(args.url)
        print(f"Navigated to: {res}")

    elif args.command == "screenshot":
        path = agent.screenshot(args.output, full_page=args.full)
        print(f"Screenshot saved: {path}")

    elif args.command == "click":
        res = agent.click(args.selector)
        print(f"Clicked {args.selector}: {res}")

    elif args.command == "click-pixel":
        res = agent.click_coords(args.x, args.y)
        print(f"Clicked pixel ({args.x}, {args.y}): {res}")

    elif args.command == "type":
        res = agent.type_text(args.selector, args.text)
        print(f"Typed into {args.selector}: {res}")

    elif args.command == "press":
        res = agent.press_key(args.key)
        print(f"Pressed key {args.key}: {res}")

    elif args.command == "scroll":
        res = agent.scroll(args.delta_x, args.delta_y)
        print(f"Scrolled (x={args.delta_x}, y={args.delta_y}): {res}")

    elif args.command == "hover":
        res = agent.hover(args.selector)
        print(f"Hovered over {args.selector}: {res}")

    elif args.command == "wait":
        res = agent.wait_for(args.selector, timeout=args.timeout)
        print(f"Waited for {args.selector}: {res}")

    elif args.command == "dom":
        text = agent.get_dom(args.selector)
        print(text[:1000])

    elif args.command == "eval":
        res = agent.eval_js(args.script)
        print(f"Result: {res}")

    elif args.command == "export-auth":
        path = agent.export_auth(args.output)
        print(f"Auth state exported to: {path}")

    elif args.command == "clear-cache":
        res = agent.clear_cache()
        print(f"Cache cleared: {res}")

    elif args.command == "clear-cookies":
        res = agent.clear_cookies()
        print(f"Cookies cleared: {res}")

    elif args.command == "reset":
        res = agent.reset_profile()
        print(f"Profile reset: {res}")

    elif args.command == "backup":
        dest = agent.backup_profile(args.name)
        print(f"Profile snapshot created: {dest}")

    elif args.command == "restore":
        res = agent.restore_profile(args.name)
        print(f"Profile restored from {args.name}: {res}")

    elif args.command in ["close", "kill"]:
        agent.close_browser()

if __name__ == "__main__":
    main()
