#!/usr/bin/env bash
# Installs the video tools. Safe to run again. Also usable as the cloud environment's Setup script.
set -e
PIP="pip install --break-system-packages -q"
apt-get update -q >/dev/null 2>&1 || true            # needed: fresh machines have empty package lists
command -v ffmpeg >/dev/null || apt-get install -y -q ffmpeg
fc-list | grep -qi montserrat || apt-get install -y -q fonts-montserrat >/dev/null 2>&1 || true
python3 -c "import faster_whisper, cv2" 2>/dev/null || $PIP faster-whisper "av<19" "opencv-contrib-python-headless<5" numpy
python3 -c "from faster_whisper import WhisperModel; WhisperModel('small', device='cpu', compute_type='int8')" >/dev/null 2>&1 \
  || echo "Speech model could not download: allow the Hugging Face domains in the cloud environment"
echo "Video tools ready: $(ffmpeg -version | head -1 | cut -d' ' -f1-3)"
