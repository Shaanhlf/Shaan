// Whiteboard reel renderer: draws the scene at any time t (seconds) on a 1080x1920 canvas.
// Pure function of t (deterministic), so the same code drives the live preview and the MP4 export.
(function () {
  const W = 1080, H = 1920;
  const FONTS = { marker: "'Permanent Marker'", hand: "'Kalam'" };

  // ---------- helpers ----------
  function rng(seed) { // small seeded random so wobble is identical every frame
    let s = seed >>> 0 || 1;
    return () => ((s = (s * 1664525 + 1013904223) >>> 0) / 4294967296);
  }
  const clamp = (v, a, b) => Math.max(a, Math.min(b, v));
  const ease = (p) => (p < 0.5 ? 4 * p * p * p : 1 - Math.pow(-2 * p + 2, 3) / 2);
  const norm = (s) => s.toLowerCase().normalize('NFD').replace(/[^a-z0-9]/g, '');

  function wobbleLine(x1, y1, x2, y2, r, amp = 2.2, steps = 14) {
    const pts = [];
    for (let i = 0; i <= steps; i++) {
      const k = i / steps;
      const j = (i === 0 || i === steps) ? 0 : (r() - 0.5) * amp;
      pts.push([x1 + (x2 - x1) * k + j * 0.3, y1 + (y2 - y1) * k + j]);
    }
    return pts;
  }

  // draw the first `p` (0..1) of a polyline, return the pen tip
  function strokePartial(ctx, pts, p, width, color) {
    let total = 0; const seg = [];
    for (let i = 1; i < pts.length; i++) {
      const d = Math.hypot(pts[i][0] - pts[i - 1][0], pts[i][1] - pts[i - 1][1]);
      seg.push(d); total += d;
    }
    let left = total * clamp(p, 0, 1);
    ctx.save();
    ctx.strokeStyle = color; ctx.lineWidth = width; ctx.lineCap = 'round'; ctx.lineJoin = 'round';
    ctx.beginPath(); ctx.moveTo(pts[0][0], pts[0][1]);
    let tip = pts[0];
    for (let i = 1; i < pts.length && left > 0; i++) {
      const k = Math.min(1, left / seg[i - 1]);
      tip = [pts[i - 1][0] + (pts[i][0] - pts[i - 1][0]) * k, pts[i - 1][1] + (pts[i][1] - pts[i - 1][1]) * k];
      ctx.lineTo(tip[0], tip[1]);
      left -= seg[i - 1];
    }
    ctx.stroke();
    ctx.restore();
    return tip;
  }

  // ---------- scene setup ----------
  let S = null; // resolved scene

  function setup(scene, words, ctx) {
    const colors = scene.colors || {};
    const col = (c) => colors[c] || c || colors.ink || '#222';
    const wl = (words.words || words).filter((w) => w.type !== 'spacing');
    let cursor = 0;
    const findCue = (cue) => {
      if (cue == null) return 0;
      if (typeof cue === 'number') return cue;
      const n = norm(cue);
      for (let i = cursor; i < wl.length; i++) {
        if (norm(wl[i].text).startsWith(n)) { cursor = i; return wl[i].start; }
      }
      console.warn('cue not found:', cue); return wl.length ? wl[wl.length - 1].end : 0;
    };
    const fontOf = (e) => `${e.font === 'hand' ? '700 ' : ''}${e.size || 44}px ${FONTS[e.font] || FONTS.marker}`;
    const measure = (text, font) => { ctx.save(); ctx.font = font; const w = ctx.measureText(text).width; ctx.restore(); return w; };
    const textDur = (txt) => clamp(txt.length * 0.045, 0.3, 1.0);

    const els = [];
    scene.elements.forEach((e0, i) => {
      const r = rng(1000 + i * 97);
      const e = { ...e0 };
      // "target": index of a text element, "part": words inside it -> position strike/line/circle on those words
      if (e.target != null && scene.elements[e.target]) {
        const tg = scene.elements[e.target], f = fontOf(tg), s = tg.size || 44;
        const idx = e.part ? tg.text.indexOf(e.part) : 0;
        const pre = measure(tg.text.slice(0, Math.max(0, idx)), f);
        const pw = measure(e.part || tg.text, f);
        if (e.type === 'circle') Object.assign(e, { x: tg.x + pre, y: tg.y - s * 0.85, w: pw, h: s * 1.0 });
        else Object.assign(e, { x1: tg.x + pre - 8, x2: tg.x + pre + pw + 8,
          y: e.type === 'strike' ? tg.y - s * 0.36 : tg.y + s * 0.3 });
      }
      const el = { ...e, i, color: col(e.color), t0: findCue(e.cue) + (e.delay || 0) };
      if (e.type === 'text') {
        el.fontStr = fontOf(e); el.w = measure(e.text, el.fontStr);
        el.rot = (r() - 0.5) * 0.012; el.dur = textDur(e.text);
        const s = e.size || 44;
        el.bbox = [e.x, e.y - s, el.w, s * 1.35];
      } else if (e.type === 'box') {
        const pad = 6, x = e.x, y = e.y, w = e.w, h = e.h;
        el.pts = [[x - pad, y], ...wobbleLine(x, y, x + w, y, r).slice(1), ...wobbleLine(x + w, y, x + w, y + h, r).slice(1),
          ...wobbleLine(x + w, y + h, x, y + h, r).slice(1), ...wobbleLine(x, y + h, x, y - pad, r).slice(1)];
        el.label = e.text || '';
        let size = e.size || 42; let f;
        while (true) { f = `${size}px ${FONTS.marker}`; if (measure(el.label, f) <= w - 40 || size < 22) break; size -= 2; }
        el.fontStr = f; el.lw = measure(el.label, f); el.lsize = size;
        el.drawDur = 0.45; el.dur = el.drawDur + (el.label ? textDur(el.label) : 0);
        el.bbox = [x - 8, y - 8, w + 16, h + 16];
        el.boxColor = e.color ? col(e.color) : col('ink');
      } else if (e.type === 'arrow') {
        el.pts = wobbleLine(e.x1, e.y, e.x2, e.y, r, 1.5, 6);
        el.dur = 0.3; el.bbox = [e.x1, e.y - 14, e.x2 - e.x1, 28];
        el.color = e.color ? col(e.color) : col('ink');
      } else if (e.type === 'strike' || e.type === 'line') {
        el.pts = wobbleLine(e.x1, e.y, e.x2, e.y + (e.type === 'strike' ? -4 : 0), r, 2.5, 10);
        el.dur = 0.35; el.bbox = [e.x1, e.y - 10, e.x2 - e.x1, 20];
      } else if (e.type === 'circle') {
        const cx = e.x + e.w / 2, cy = e.y + e.h / 2, rx = e.w / 2 + 28, ry = e.h / 2 + 16;
        el.pts = [];
        for (let k = 0; k <= 60; k++) {
          const a = -Math.PI * 0.6 + (k / 60) * Math.PI * 2.15; const j = 1 + (r() - 0.5) * 0.03;
          el.pts.push([cx + Math.cos(a) * rx * j, cy + Math.sin(a) * ry * j]);
        }
        el.dur = 0.6; el.bbox = [cx - rx, cy - ry, rx * 2, ry * 2];
      } else if (e.type === 'badge') {
        const R = 30; el.pts = [];
        for (let k = 0; k <= 40; k++) { const a = -Math.PI / 2 + (k / 40) * Math.PI * 2.1; el.pts.push([e.x + Math.cos(a) * R, e.y + Math.sin(a) * R]); }
        el.fontStr = `36px ${FONTS.marker}`; el.lw = measure(e.text, el.fontStr);
        el.dur = 0.4; el.bbox = [e.x - R, e.y - R, R * 2, R * 2];
      }
      els.push(el);
    });

    // camera keyframes: frame everything drawn so far
    const kfs = [];
    let bb = null;
    [...els].sort((a, b) => a.t0 - b.t0).forEach((el) => {
      const [x, y, w, h] = el.bbox;
      bb = bb ? [Math.min(bb[0], x), Math.min(bb[1], y), Math.max(bb[2], x + w), Math.max(bb[3], y + h)] : [x, y, x + w, y + h];
      const bw = bb[2] - bb[0], bh = bb[3] - bb[1];
      const s = Math.min(1.45, (W - 140) / bw, (H * 0.78) / bh);
      const cam = { s, cx: (bb[0] + bb[2]) / 2, cy: (bb[1] + bb[3]) / 2 };
      kfs.push({ t: Math.max(0, el.t0 - 0.15), cam });
    });
    const camAt = []; // camera value at the start of each keyframe
    const lerpCam = (a, b, k) => ({ s: a.s + (b.s - a.s) * k, cx: a.cx + (b.cx - a.cx) * k, cy: a.cy + (b.cy - a.cy) * k });
    const camVal = (t, upto) => {
      let c = kfs[0].cam;
      for (let i = 1; i < upto; i++) { if (kfs[i].t > t) break; c = lerpCam(camAt[i], kfs[i].cam, ease(clamp((t - kfs[i].t) / 0.9, 0, 1))); }
      return c;
    };
    kfs.forEach((k, i) => { camAt[i] = i === 0 ? k.cam : camVal(k.t, i); });

    const audioEnd = wl.length ? wl[wl.length - 1].end : 0;
    const lastDraw = Math.max(...els.map((e) => e.t0 + e.dur));
    S = { scene, els, kfs, camera: (t) => camVal(t, kfs.length), colors: { ink: col('ink') },
      duration: Math.max(audioEnd, lastDraw) + 1.2 };
    return S;
  }

  // ---------- drawing ----------
  function drawBackground(ctx) {
    ctx.fillStyle = (S && S.scene.background) || '#fdfdfb'; ctx.fillRect(0, 0, W, H);
    const g = ctx.createRadialGradient(W / 2, H * 0.38, 200, W / 2, H * 0.5, H * 0.75);
    g.addColorStop(0, 'rgba(255,255,255,0)'); g.addColorStop(1, 'rgba(30,35,45,0.05)');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  }

  function drawText(ctx, el, p, t) {
    ctx.save();
    ctx.translate(el.x, el.y); ctx.rotate(el.rot);
    ctx.font = el.fontStr; ctx.fillStyle = el.color; ctx.textBaseline = 'alphabetic';
    const s = el.size || 44;
    ctx.beginPath(); ctx.rect(-10, -s * 1.2, el.w * p + 6 + (p >= 1 ? 30 : 0), s * 1.7); ctx.clip();
    ctx.fillText(el.text, 0, 0);
    ctx.restore();
    return [el.x + el.w * p, el.y - s * 0.35 + Math.sin(t * 38) * s * 0.22];
  }

  function drawLabel(ctx, el, p, t) { // centred text inside a box
    const x = el.x + (el.w - el.lw) / 2, y = el.y + el.h / 2 + el.lsize * 0.36;
    ctx.save(); ctx.font = el.fontStr; ctx.fillStyle = el.boxColor;
    ctx.beginPath(); ctx.rect(x - 6, el.y, el.lw * p + 6, el.h); ctx.clip();
    ctx.fillText(el.label, x, y); ctx.restore();
    return [x + el.lw * p, y - el.lsize * 0.35 + Math.sin(t * 38) * el.lsize * 0.22];
  }

  function drawEl(ctx, el, t) {
    const lt = t - el.t0; if (lt < 0) return null;
    const p = clamp(lt / el.dur, 0, 1);
    let tip = null;
    switch (el.type) {
      case 'text': tip = drawText(ctx, el, p, t); break;
      case 'box': {
        const pb = clamp(lt / el.drawDur, 0, 1);
        ctx.save(); ctx.translate(4, 5);
        strokePartial(ctx, el.pts, ease(pb), 7, 'rgba(0,0,0,0.07)'); ctx.restore();
        tip = strokePartial(ctx, el.pts, ease(pb), 5.5, el.boxColor);
        strokePartial(ctx, el.pts.map(([x, y]) => [x + 1.5, y + 1.2]), ease(pb), 2, el.boxColor);
        if (el.label && lt > el.drawDur) tip = drawLabel(ctx, el, clamp((lt - el.drawDur) / (el.dur - el.drawDur), 0, 1), t);
        break;
      }
      case 'arrow': {
        tip = strokePartial(ctx, el.pts, p, 4.5, el.color);
        if (p >= 1) {
          strokePartial(ctx, [[el.x2 - 16, el.y - 11], [el.x2, el.y], [el.x2 - 16, el.y + 11]], 1, 4.5, el.color);
        }
        break;
      }
      case 'strike': case 'line': tip = strokePartial(ctx, el.pts, ease(p), el.type === 'strike' ? 7 : 5, el.color); break;
      case 'circle': tip = strokePartial(ctx, el.pts, ease(p), 5, el.color); break;
      case 'badge': {
        tip = strokePartial(ctx, el.pts, ease(p), 5, el.color);
        if (p > 0.6) {
          ctx.save(); ctx.globalAlpha = clamp((p - 0.6) / 0.3, 0, 1);
          ctx.font = el.fontStr; ctx.fillStyle = el.color; ctx.fillText(el.text, el.x - el.lw / 2, el.y + 13); ctx.restore();
        }
        break;
      }
    }
    return p < 1 ? { tip, color: el.type === 'box' ? el.boxColor : el.color } : null;
  }

  function drawPen(ctx, x, y, color, alpha) {
    if (alpha <= 0) return;
    ctx.save(); ctx.globalAlpha = alpha; ctx.translate(x, y); ctx.rotate(0.95);
    ctx.shadowColor = 'rgba(0,0,0,0.18)'; ctx.shadowBlur = 18; ctx.shadowOffsetX = 10; ctx.shadowOffsetY = 14;
    // tip
    ctx.fillStyle = color; ctx.beginPath(); ctx.moveTo(0, 0); ctx.lineTo(26, -9); ctx.lineTo(26, 9); ctx.closePath(); ctx.fill();
    // body
    ctx.fillStyle = '#f4f4f2'; ctx.strokeStyle = '#2b2c30'; ctx.lineWidth = 2.5;
    ctx.beginPath(); ctx.roundRect(26, -16, 190, 32, 6); ctx.fill(); ctx.shadowColor = 'transparent'; ctx.stroke();
    // grip band + cap in ink colour
    ctx.fillStyle = color; ctx.fillRect(60, -16, 14, 32);
    ctx.beginPath(); ctx.roundRect(196, -17, 44, 34, 8); ctx.fill(); ctx.stroke();
    ctx.restore();
  }

  let lastPen = null; // remembered pen position for smooth hide
  function render(ctx, t) {
    if (!S) return;
    drawBackground(ctx);
    const cam = S.camera(t);
    ctx.save();
    ctx.translate(W / 2, H * 0.47); ctx.scale(cam.s, cam.s); ctx.translate(-cam.cx, -cam.cy);
    let active = null;
    for (const el of S.els) { const a = drawEl(ctx, el, t); if (a) active = a; }
    // pen: shown while drawing, fades shortly after
    let lastEnd = -1, lastEl = null;
    for (const el of S.els) if (el.t0 <= t && el.t0 + el.dur > lastEnd) { lastEnd = el.t0 + el.dur; lastEl = el; }
    if (active) { lastPen = active; drawPen(ctx, active.tip[0], active.tip[1], active.color, 1); }
    else if (lastPen && t - lastEnd < 0.35) {
      const k = (t - lastEnd) / 0.35;
      drawPen(ctx, lastPen.tip[0] + k * 60, lastPen.tip[1] + k * 90, lastPen.color, 1 - k);
    }
    ctx.restore();
    if (S.scene.handle) {
      // handle sits at the top (default, clear of IG's caption area) or bottom
      const top = S.scene.handlePosition !== 'bottom';
      ctx.save(); ctx.font = `700 36px ${FONTS.hand}`; ctx.fillStyle = 'rgba(40,40,45,0.42)';
      ctx.textAlign = 'center'; ctx.fillText(S.scene.handle, W / 2, top ? 140 : H - 120); ctx.restore();
    }
  }

  window.Board = { W, H, setup, render, get duration() { return S ? S.duration : 0; } };
})();
