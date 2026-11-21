# Whiteboard Reel (gaya "papan putih + marker")

Enjin kecil untuk buat reel 1080x1920 gaya whiteboard: tulisan tangan muncul ikut suara, kotak dan anak panah dilukis, dan kamera zoom out bila papan makin penuh. Suara dari ElevenLabs (voice **Shaan malay**).

## Research: reel asal (@coachkimii_, "Turun Berat ≠ Hilang Lemak")

**Apa yang ada dalam video (53 s, 720x1280, 30 fps):**
- Background putih kelabu muda dengan sedikit bayang di tepi.
- Font tangan huruf besar (gaya *Permanent Marker*) untuk kotak dan tajuk. Font tulisan tangan kecil untuk nota ("bukan otot", "nasi pun boleh!").
- 4 warna sahaja: hitam (kotak), merah (tajuk / pangkah), hijau (hasil), biru (nota, garis bawah).
- Satu marker 3D ikut hujung tulisan. Warna penutupnya ikut warna dakwat.
- Struktur "rantai": kotak ditambah satu-satu (+), anak panah ke hasil, dan hasil lama dipangkah bila ada hasil baru yang lebih baik.
- Kamera mula zoom-in, lepas tu perlahan-lahan zoom out supaya semua kandungan muat.
- Setiap perkataan muncul **tepat bila disebut** dalam voiceover.
- Penutup: "KOMEN PLAN" (CTA), lepas tu skrin gelap dengan logo IG dan handle.

**Macam mana dia buat (anggaran, sebab kod dia tak didedahkan):**
Gaya ni boleh dibuat dengan app animasi whiteboard (VideoScribe, Doodly) atau dengan kod (HTML canvas / Remotion) yang render setiap frame. Petunjuknya: marker tak pernah goyang secara semula jadi, tulisan didedahkan kiri ke kanan dengan "mask", dan timing sangat tepat dengan perkataan. Itu tanda tulisan diselaraskan dengan transkrip yang ada cap masa setiap perkataan. Suara tu kemungkinan suara dia sendiri atau AI voice.

## Cara enjin ni berfungsi

1. **Skrip → suara**: ElevenLabs (`eleven_multilingual_v2`, voice *Shaan malay*) → `audio/voice.mp3`
2. **Suara → cap masa perkataan**: ElevenLabs Scribe → `audio/words.json`
3. **`scene.json`**: senarai apa nak dilukis. Setiap item ada `cue` (perkataan dalam skrip yang memulakannya).
4. **`board.js`**: lukis papan pada masa *t*: tulisan, kotak bergoyang (hand-drawn), anak panah, pangkah, bulatan, nombor, marker, dan kamera.
5. **`render.js`**: buka page dalam Chromium (Playwright), ambil 30 frame sesaat, gabung dengan suara guna ffmpeg → `out/reel.mp4`

## Guna

```bash
npm install
node render.js --serve        # preview dengan suara: http://localhost:8080
node render.js --still 12     # satu frame untuk semak layout -> out/still.jpg
node render.js                # video penuh -> out/reel.mp4
```

## Buat video baru

1. Tulis skrip baru dan jana suara di ElevenLabs dengan voice *Shaan malay*. Simpan sebagai `audio/voice.mp3`.
2. Transcribe dengan ElevenLabs Speech-to-Text (format words JSON). Simpan sebagai `audio/words.json`.
3. Ubah `scene.json`:
   - `text`: `text`, `x`, `y`, `size`, `color` (`ink`/`red`/`green`/`blue`/`note`), `font: "hand"` untuk tulisan kecil
   - `box`: `text`, `x`, `y`, `w`, `h` (saiz tulisan mengecil sendiri kalau panjang)
   - `arrow`: `x1`, `x2`, `y`
   - `strike` / `line` / `circle`: `target` (nombor item text) + `part` (perkataan yang nak dipangkah / digaris / dibulatkan)
   - `badge`: nombor dalam bulatan
   - `cue`: perkataan dalam voiceover yang mulakan item tu (dicari ikut turutan), `delay` dalam saat
   - `handle`: letak `@username` awak untuk watermark kecil di bawah
4. `node render.js`
