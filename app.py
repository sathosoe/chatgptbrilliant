#!/usr/bin/env python3
"""
Frame ✕ Noa ✕ OpenAI 連携用サーバ
  1. Noa から multipart/form-data で audio / messages / noa_system_prompt が届く
  2. 必要に応じ ffmpeg で 16 kHz mono WAV へ変換
  3. Whisper (whisper-1 / gpt-4o-transcribe 等) で文字起こし
  4. ChatGPT (gpt-4 など) で応答生成
  5. JSON を返却 (Noaアプリが期待するキャメルケースのキー)
"""
import json, os, subprocess, tempfile, logging
from flask import Flask, request, jsonify
from openai import OpenAI

# ---------- OpenAI 初期化 ----------
client = OpenAI()                      # OPENAI_API_KEY は環境変数で読む

# ---------- Flask ----------
app = Flask(__name__)
app.logger.setLevel(logging.INFO)
# 【推奨】jsonify が日本語を ASCII エスケープしないように設定
app.config = False

@app.route("/", methods=)
def healthcheck():
    return "OK"

@app.route("/", methods=)
def noa_proxy():
    log = app.logger
    log.info("=== New request ===")

    # 1) 受信 ---------------------------------------------------------------
    audio_file = request.files.get("audio")
    if audio_file is None:
        return jsonify(error="No audio field"), 400

    system_prompt = request.form.get("noa_system_prompt", "")
    history_json  = request.form.get("messages", "")

    # 2) 一時ファイル保存 & ffmpeg ------------------------------------------
    with tempfile.NamedTemporaryFile(suffix=".input", delete=False) as src:
        audio_file.save(src.name)
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as dst:
        pass  # dst だけ確保

    ffmpeg_cmd = [
        "ffmpeg", "-y", "-i", src.name,
        "-ar", "16000", "-ac", "1", dst.name
    ]
    log.info("ffmpeg: %s", " ".join(ffmpeg_cmd))
    try:
        subprocess.run(ffmpeg_cmd, check=True, capture_output=True)
    except subprocess.CalledProcessError as e:
        log.error("ffmpeg error: %s", e.stderr.decode()[:200])
        return jsonify(error="ffmpeg failed"), 500

    # 3) Whisper -----------------------------------------------------------
    try:
        with open(dst.name, "rb") as wav:
            transcript_text = client.audio.transcriptions.create(
                model=os.getenv("WHISPER_MODEL", "whisper-1"),
                file=wav,
                response_format="text"
            )
        log.info("Transcript: %s", transcript_text[:120])
    except Exception as e:
        log.exception("Whisper API error")
        return jsonify(error=f"Whisper API: {e}"), 500
    finally:
        os.unlink(src.name); os.unlink(dst.name)   # ゴミ掃除

    # 4) ChatGPT -----------------------------------------------------------
    messages =
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    try:
        for m in json.loads(history_json):
            if all(k in m for k in ("role", "content")):
                messages.append({"role": m["role"], "content": m["content"]})
    except json.JSONDecodeError:
        log.warning("messages JSON parse error — 無視して続行")

    messages.append({"role": "user", "content": transcript_text})

    try:
        chat_resp = client.chat.completions.create(
            model=os.getenv("CHAT_MODEL", "gpt-4o-mini"),
            messages=messages
        )
        answer = chat_resp.choices.message.content.strip()
        log.info("Answer: %s", answer[:120])
    except Exception as e:
        log.exception("ChatCompletion error")
        return jsonify(error=f"Chat API: {e}"), 500

    # 5) Frame/Noa 形式で返却 ------------------------------------------------
    # 【修正点】JSONのキーをNoaアプリが期待するキャメルケースに変更
    response_body = {
        "reply":        answer,
        "displayText":  answer,
        "replyAudio":   "",       # Noneではなく空文字列を返す
        "topicChanged": False
    }
    log.info("Returning JSON for Noa: %s", response_body)

    # 【修正点】Flask推奨の jsonify() を使用してレスポンスを生成
    return jsonify(response_body)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=False)
