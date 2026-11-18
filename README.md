# 😎 Meme Studio

[![Smoke test](https://github.com/Sandman-2-2/meme-studio/actions/workflows/smoke-test.yml/badge.svg)](https://github.com/Sandman-2-2/meme-studio/actions/workflows/smoke-test.yml)

A personal meme maker: classic templates, AI captions (Google Gemini), a full caption editor, multi-panel builder, AI scene generator, and a private vault.

**Live site:** https://sandman-2-2.github.io/meme-studio/

## Features
- **~120 classic templates** from imgflip, 75 hand-mapped (incl. 11 Simpsons) with example captions; the rest are auto-mapped by Gemini vision the first time they're used.
- **Smarter generation:** Gemini brainstorms 8 candidates, scores them, and keeps the best 4. Per-meme **🔁 New take** and **🔀 Swap template**.
- **🌎 My World:** inside jokes, names and saved custom themes the AI can weave in.
- **🎲 Surprise me:** AI invents a fresh situation for the selected theme each time.
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
| `tests/smoke_test.py` | 24 automated checks with Gemini/imgflip mocked; runs on every push via GitHub Actions |
| `.nojekyll` | Serve files as-is on GitHub Pages |

Run tests locally: `pip install playwright && python -m playwright install chromium && python tests/smoke_test.py`
