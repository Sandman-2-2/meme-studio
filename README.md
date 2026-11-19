# 😎 Meme Studio

[![Smoke test](https://github.com/Sandman-2-2/meme-studio/actions/workflows/smoke-test.yml/badge.svg)](https://github.com/Sandman-2-2/meme-studio/actions/workflows/smoke-test.yml)

A personal meme maker: classic templates, AI captions (Google Gemini), a full caption editor, multi-panel builder, AI scene generator, and a private vault.

**Live site:** https://sandman-2-2.github.io/meme-studio/

## Features
- **~120 classic templates** from imgflip, 75 hand-mapped (incl. 11 Simpsons) with example captions; the rest are auto-mapped by Gemini vision the first time they're used.
- **Smarter generation:** Gemini brainstorms 8 candidates, scores them, and keeps the best 4. Per-meme **🔁 New take** and **🔀 Swap template**.
- **🌎 My World:** inside jokes, names and saved custom themes the AI can weave in.
- **🎲 Surprise me:** a random spark (a corner of everyday life × a comedy lens, plus the season) so each surprise is a whole different take.
- **💡 Inspire me:** 6 idea chips from different areas of life; tap one to make memes.
- **🔄 Try again:** reruns the whole prompt. The app remembers jokes and templates already shown for each prompt and tells the AI to avoid them; random comedy lenses push it to new angles (🔁 New take does the same).
- **🔥 Trending:** what's hot right now on Reddit (r/popular), Bluesky trending topics, Mastodon trending tags/links, and Wikipedia's most-looked-up pages. Listed instantly with no AI wait; each source loads on its own (8s cap). Skips NSFW, tragedies and partisan fights. Paste any link (Gemini URL reading) or text as a fallback.
- **📱 Surface Duo / foldables:** edge-to-edge with safe-area padding on one screen. Spanned across both screens, the app runs on the left and your memes (and the editor) live on the right, split around the hinge.
- **Editor:** drag, corner-resize, undo/redo (Ctrl+Z), auto-fit text, emoji stickers, image layers, top-bar caption style, ✨ Punch up.
- **Robust:** auto-discovers current Gemini models, skips busy/over-quota models, remembers what works, tracks today's usage.
- **Offline-ready PWA:** service worker caches the app and templates; shows a "new version ready" banner after updates.
- **Vault + history** stored in IndexedDB (hundreds of memes), JSON backup/restore.

## Using it
- Tap **Add AI key** and paste a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey). Stored only in your browser.
- On iPhone/Android: open the site, Share → **Add to Home Screen**.

## Files
| File | Purpose |
|---|---|
| `index.html` | The whole app (HTML, CSS, JS) |
| `sw.js` | Service worker (offline + updates). **Bump `VERSION` on every deploy** so the update banner appears. |
| `manifest.webmanifest`, `*.png`, `icon.svg` | App name, colors and icons |
| `tests/smoke_test.py` | automated checks with Gemini/imgflip mocked; runs on every push via GitHub Actions |
| `.nojekyll` | Serve files as-is on GitHub Pages |

Run tests locally: `pip install playwright && python -m playwright install chromium && python tests/smoke_test.py`
