"""Meme Studio smoke tests.

Runs the real index.html in headless Chromium with Gemini and imgflip mocked,
so it needs no API key and no network. Used locally and by GitHub Actions.
Run: python tests/smoke_test.py
"""
import asyncio, json, os, re, sys, threading, http.server, socketserver, functools
from playwright.async_api import async_playwright

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FIX = open(os.path.join(ROOT, "tests", "fixture.jpg"), "rb").read()
STICKER = os.path.join(ROOT, "tests", "sticker.png")
CORS = {"access-control-allow-origin": "*"}
CHROME = os.environ.get("CHROME_PATH")  # optional local Chrome
results, failures = [], []

def check(name, cond, detail=""):
    (results if cond else failures).append(name)
    print(("PASS " if cond else "FAIL ") + name + (f"  ({detail})" if detail and not cond else ""))

def serve():
    class Quiet(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a): pass
    handler = functools.partial(Quiet, directory=ROOT)
    httpd = socketserver.TCPServer(("127.0.0.1", 0), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd

class FakeGemini:
    """Answers like Gemini: model list, captions JSON, vision box maps."""
    def __init__(self):
        self.calls = []
        self.fail = {}  # model -> status to return
    async def handle(self, route):
        r = route.request
        if r.method == "GET":
            models = ["gemini-3.8-flash", "gemini-3.7-flash", "gemini-3.5-flash-lite", "gemini-3.1-flash-lite-image"]
            return await route.fulfill(status=200, headers=CORS, body=json.dumps({"models": [{"name": "models/" + m, "supportedGenerationMethods": ["generateContent"]} for m in models]}))
        model = re.search(r"models/([^:]+):", r.url).group(1)
        body = json.loads(r.post_data)
        parts = body["contents"][0]["parts"]
        text = parts[0]["text"]
        self.calls.append((model, text))
        if model in self.fail:
            return await route.fulfill(status=self.fail[model], headers=CORS, body=json.dumps({"error": {"message": "Quota exceeded for metric PerDay" if self.fail[model] == 429 else "high demand"}}))
        if '"ok":true' in text and len(text) < 60:
            out = {"ok": True}
        elif '"boxes"' in text:
            out = {"vibe": "Auto-described format", "boxes": [{"label": "Top", "x": .5, "y": .1, "w": .9, "style": "light", "size": "m"}, {"label": "Bottom", "x": .5, "y": .9, "w": .9, "style": "dark", "size": "l"}]}
        elif "Rewrite this meme with a completely DIFFERENT joke" in text:
            tid = re.findall(r'"templateId":"([^"]+)"', text)[-1]
            out = {"candidates": [{"templateId": tid, "captions": ["NEW TAKE A", "NEW TAKE B"], "score": 9}]}
        elif "Re-tell this same joke" in text:
            out = {"candidates": [{"templateId": "55311130", "captions": ["SWAPPED", "This is fine"], "score": 8}]}
        elif "funnier ways" in text:
            out = {"options": [{"style": "Shorter", "text": "Punchier"}]}
        else:
            # brainstorm: scores out of order on purpose; one unmapped API template id (999)
            out = {"situation": "AI invented situation", "candidates": [
                {"templateId": "181913649", "captions": ["low", "score"], "score": 2},
                {"templateId": "101470", "captions": ["best one", "Aliens"], "score": 10},
                {"templateId": "55311130", "captions": ["mid", "fine"], "score": 6},
                {"templateId": "129242436", "captions": ["hot take"], "score": 8},
                {"templateId": "999", "captions": ["api top", "api bottom"], "score": 9},
                {"templateId": "nope", "captions": ["bad id"], "score": 10}]}
        await route.fulfill(status=200, headers=CORS, body=json.dumps({"candidates": [{"content": {"parts": [{"text": json.dumps(out)}]}}]}))

async def imgflip_api(route):
    memes = [{"id": "999", "name": "Unmapped Test Meme", "url": "https://i.imgflip.com/test999.jpg", "width": 600, "height": 500, "box_count": 2}]
    await route.fulfill(status=200, headers=CORS, body=json.dumps({"success": True, "data": {"memes": memes}}))

async def imgflip_img(route):
    await route.fulfill(status=200, headers={**CORS, "content-type": "image/jpeg"}, body=FIX)

async def main():
    httpd = serve()
    base = f"http://localhost:{httpd.server_address[1]}/index.html"
    gem = FakeGemini()
    async with async_playwright() as p:
        b = await p.chromium.launch(**({"executable_path": CHROME} if CHROME else {}))
        ctx = await b.new_context(viewport={"width": 1280, "height": 900}, service_workers="block")
        await ctx.route("**/generativelanguage.googleapis.com/**", gem.handle)
        await ctx.route("**/api.imgflip.com/**", imgflip_api)
        await ctx.route("**/i.imgflip.com/**", imgflip_img)
        await ctx.route("**/fonts.googleapis.com/**", lambda r: r.fulfill(status=200, body="", headers={"content-type": "text/css"}))
        pg = await ctx.new_page()
        errs = []
        pg.on("pageerror", lambda e: errs.append(str(e)))
        await pg.goto(base); await pg.wait_for_timeout(1500)

        n = await pg.evaluate("TEMPLATES.length")
        check("templates load (curated + imgflip list)", n >= 76, n)
        check("starter memes render", await pg.locator("#results .meme-card").count() == 4)

        # Instant mode (no key)
        await pg.fill("#prompt", "test situation"); await pg.click("#generateBtn"); await pg.wait_for_timeout(800)
        check("instant mode works without a key", await pg.locator("#results .meme-card").count() == 4)

        # Key + diagnostics test
        await pg.click("#aiChip"); await pg.fill("#keyInput", "AQ.test-key"); await pg.click("#keyTest"); await pg.wait_for_timeout(1200)
        diag = await pg.inner_text("#keyDiag")
        check("key test passes", "AI is ready" in diag, diag)
        await pg.click("#settingsClose")

        # My World
        await pg.click("#worldBtn"); await pg.fill("#worldNotes", "Our mascot is the Tigers."); await pg.click("#worldSave")

        # Generate: brainstorm + scoring + unmapped auto-map
        gem.calls.clear()
        await pg.fill("#prompt", "copier jams"); await pg.click("#generateBtn"); await pg.wait_for_timeout(2500)
        titles = [t.lower() for t in await pg.locator("#results .mc-top span").all_inner_texts()]
        check("best-scored meme is first", titles and titles[0] == "ancient aliens", titles)
        check("bad template ids ignored, 4 distinct", len(titles) == 4 and len(set(titles)) == 4, titles)
        prompt_text = next((t for m, t in gem.calls if "Brainstorm 8" in t), "")
        check("prompt includes template examples", "example:" in prompt_text)
        check("prompt includes My World", "Tigers" in prompt_text)
        check("unmapped template auto-mapped via vision", await pg.evaluate("!!tplById('999').autoMapped"))
        check("auto-map cached", "999" in (await pg.evaluate("localStorage.getItem('memeStudio.autoMaps.v1')") or ""))

        # History strip
        await pg.wait_for_timeout(300)
        check("recent history saved", await pg.locator("#historyList button").count() >= 1)

        # Per-card remix
        await pg.locator("#results .meme-card").nth(1).locator("[data-a=take]").click(); await pg.wait_for_timeout(1200)
        texts = await pg.evaluate("[...document.querySelectorAll('#results .meme-card')].map(c => c._spec.layers.map(l => l.text).join('|'))")
        check("New take rewrites one card", any("NEW TAKE A" in t for t in texts), texts)
        await pg.locator("#results .meme-card").nth(0).locator("[data-a=swap]").click(); await pg.wait_for_timeout(1200)
        t3 = await pg.locator("#results .meme-card").nth(0).locator(".mc-top span").inner_text()
        check("Swap template changes template", t3.lower() == "this is fine", t3)

        # Surprise
        await pg.click("#surpriseBtn"); await pg.wait_for_timeout(1500)
        check("Surprise fills invented situation", await pg.input_value("#prompt") == "AI invented situation")

        # Editor: undo/redo, emoji, image, resize
        await pg.locator("#results .meme-card canvas").first.click(); await pg.wait_for_timeout(400)
        n0 = await pg.evaluate("ED.spec.layers.length")
        await pg.click("#addEmoji"); await pg.locator("#emojiPicker button").first.click()
        await pg.set_input_files("#addImage", STICKER); await pg.wait_for_timeout(500)
        check("emoji + image layers added", await pg.evaluate("ED.spec.layers.length") == n0 + 2)
        await pg.click("#edUndo"); await pg.click("#edUndo")
        check("undo works", await pg.evaluate("ED.spec.layers.length") == n0)
        await pg.click("#edRedo")
        check("redo works", await pg.evaluate("ED.spec.layers.length") == n0 + 1)
        # resize: drag selected layer's handle
        box = await pg.evaluate("(() => { const b = ED.info.boxes[ED.sel]; const r = edCanvas.getBoundingClientRect(); const s = r.width / edCanvas.width; return { x: r.left + b.handle.x * s - 2, y: r.top + b.handle.y * s - 2 }; })()")
        size0 = await pg.evaluate("ED.spec.layers[ED.sel].size")
        await pg.mouse.move(box["x"], box["y"]); await pg.mouse.down(); await pg.mouse.move(box["x"] + 60, box["y"] + 60, steps=5); await pg.mouse.up()
        check("resize handle scales layer", await pg.evaluate("ED.spec.layers[ED.sel].size") > size0)
        await pg.click("#edVault"); await pg.wait_for_timeout(500)
        await pg.click("#edClose")

        # Vault (IndexedDB) persists across reload
        await pg.reload(); await pg.wait_for_timeout(1200)
        check("vault persists in IndexedDB", await pg.inner_text("#vaultCount") == "1")
        check("history persists", await pg.locator("#historyList button").count() >= 1)

        # Quota-aware: newest model 429 PerDay -> skipped and rested
        gem.fail = {"gemini-3.8-flash": 429}
        await pg.evaluate("localStorage.removeItem('memeStudio.goodModel')")
        await pg.fill("#prompt", "quota"); await pg.click("#generateBtn"); await pg.wait_for_timeout(2000)
        check("quota error skips to next model", "Fresh memes" in await pg.inner_text("#resultsTitle"))
        check("rate-limited model is resting", await pg.evaluate("coolingDown('gemini-3.8-flash')"))

        check("no JavaScript errors", not errs, errs[:3])
        await ctx.close()

        # Service worker: offline reload serves the app shell
        ctx2 = await b.new_context()
        await ctx2.route("**/i.imgflip.com/**", imgflip_img)
        await ctx2.route("**/api.imgflip.com/**", imgflip_api)
        pg2 = await ctx2.new_page()
        await pg2.goto(base); await pg2.wait_for_timeout(1500)
        await pg2.evaluate("navigator.serviceWorker.ready")
        await pg2.reload(); await pg2.wait_for_timeout(800)
        await ctx2.set_offline(True)
        try:
            await pg2.reload(); await pg2.wait_for_timeout(800)
            ok = await pg2.locator("h1").inner_text()
        except Exception as e:
            ok = str(e)
        check("app opens offline (service worker)", "MEME STUDIO" in ok, ok[:80])
        await ctx2.close(); await b.close()
    httpd.shutdown()
    print(f"\n{len(results)} passed, {len(failures)} failed")
    sys.exit(1 if failures else 0)

asyncio.run(main())
