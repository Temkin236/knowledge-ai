"""Capture high-resolution application screenshots using headless Chromium and Chrome DevTools Protocol."""

import asyncio
import base64
import json
import os
import subprocess
import time
import urllib.request
import websockets

SCREENSHOTS_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../docs/screenshots"))
os.makedirs(SCREENSHOTS_DIR, exist_ok=True)

msg_id = 0

async def cdp_call(ws, method, params=None):
    global msg_id
    msg_id += 1
    call_id = msg_id
    payload = {"id": call_id, "method": method, "params": params or {}}
    await ws.send(json.dumps(payload))
    while True:
        resp_raw = await ws.recv()
        resp = json.loads(resp_raw)
        if resp.get("id") == call_id:
            if "error" in resp:
                raise RuntimeError(f"CDP error on {method}: {resp['error']}")
            return resp.get("result", {})

async def capture():
    proc = subprocess.Popen([
        "/usr/bin/chromium",
        "--headless=new",
        "--remote-debugging-port=9222",
        "--no-sandbox",
        "--disable-gpu",
        "--window-size=1440,900",
        "--force-device-scale-factor=1.5",
        "about:blank",
    ])
    time.sleep(1.5)

    try:
        tabs = json.loads(urllib.request.urlopen("http://localhost:9222/json").read())
        ws_url = tabs[0]["webSocketDebuggerUrl"]
        async with websockets.connect(ws_url, max_size=20 * 1024 * 1024) as ws:
            await cdp_call(ws, "Page.enable")
            await cdp_call(ws, "Runtime.enable")
            await cdp_call(ws, "Emulation.setDeviceMetricsOverride", {
                "width": 1440,
                "height": 900,
                "deviceScaleFactor": 1.5,
                "mobile": False,
            })

            # 1. Landing Page
            print("[*] Navigating to Landing Page...")
            await cdp_call(ws, "Page.navigate", {"url": "http://localhost:5173/"})
            await asyncio.sleep(2.0)
            res = await cdp_call(ws, "Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(SCREENSHOTS_DIR, "landing-page.png"), "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"[+] Saved landing-page.png ({len(res['data'])} bytes)")

            # Set auth credentials in localStorage
            print("[*] Setting dev authentication state...")
            setup_auth_js = """
            localStorage.setItem('knowledge_ai_token', 'dev-token');
            localStorage.setItem('knowledge_ai_user', JSON.stringify({
                id: '00000000-0000-0000-0000-000000000001',
                email: 'dev@knowledge.ai',
                displayName: 'Dev Engineer'
            }));
            """
            await cdp_call(ws, "Runtime.evaluate", {"expression": setup_auth_js})

            # 2. Dashboard Page
            print("[*] Navigating to Dashboard...")
            await cdp_call(ws, "Page.navigate", {"url": "http://localhost:5173/dashboard"})
            await asyncio.sleep(2.5)
            res = await cdp_call(ws, "Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(SCREENSHOTS_DIR, "dashboard.png"), "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"[+] Saved dashboard.png")

            # 3. Knowledge Base Page
            print("[*] Navigating to Knowledge Base...")
            await cdp_call(ws, "Page.navigate", {"url": "http://localhost:5173/knowledge-base"})
            await asyncio.sleep(2.5)
            res = await cdp_call(ws, "Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(SCREENSHOTS_DIR, "knowledge-base.png"), "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"[+] Saved knowledge-base.png")

            # 4. Chat Page
            print("[*] Navigating to Chat...")
            await cdp_call(ws, "Page.navigate", {"url": "http://localhost:5173/chat"})
            await asyncio.sleep(2.5)
            # Click on the citation badge if available
            click_citation_js = """
            (() => {
                const badge = document.querySelector('button[title*=\"citation\"], button[class*=\"emerald\"], span[class*=\"citation\"], button:has(svg)');
                const citationBtn = Array.from(document.querySelectorAll('button')).find(b => b.textContent && b.textContent.includes('1'));
                if (citationBtn) {
                    citationBtn.click();
                    return 'clicked citation [1]';
                }
                return 'no citation button found';
            })()
            """
            eval_res = await cdp_call(ws, "Runtime.evaluate", {"expression": click_citation_js})
            print(f"[*] Citation click result: {eval_res.get('result', {}).get('value')}")
            await asyncio.sleep(1.5)
            res = await cdp_call(ws, "Page.captureScreenshot", {"format": "png"})
            with open(os.path.join(SCREENSHOTS_DIR, "chat-citations.png"), "wb") as f:
                f.write(base64.b64decode(res["data"]))
            print(f"[+] Saved chat-citations.png")

    finally:
        proc.terminate()
        print("[*] Screenshot capture completed.")

if __name__ == "__main__":
    asyncio.run(capture())
