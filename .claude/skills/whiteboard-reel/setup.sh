#!/usr/bin/env bash
# Installs what the whiteboard reel engine needs. Safe to run again.
set -e
E="$(cd "$(dirname "$0")" && pwd)/engine"
command -v ffmpeg >/dev/null || { apt-get update -q >/dev/null 2>&1 || true; apt-get install -y -q ffmpeg; }
[ -d "$E/node_modules/@fontsource/kalam" ] || (cd "$E" && npm install --silent)
node -e "require('playwright')" 2>/dev/null || echo "Playwright not found: run 'npm i -g playwright' (Chromium is pre-installed in cloud sessions)"
echo "Whiteboard engine ready"
