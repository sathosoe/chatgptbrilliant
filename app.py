#!/usr/bin/env python3
import json, os, subprocess, tempfile, logging, time
from flask import Flask, request, jsonify
from openai import OpenAI
client = OpenAI()

FAST_WHISPER = os.getenv("WHISPER_MODEL", "gpt-4o-mini-transcribe")
CHAT_MODEL   = os.getenv("CHAT_MODEL",   "gpt-4o-mini")

app = Flask(__name__)
app.logger.setLevel(logging.INFO)

@app.route("/", methods=["GET"])
def health(): return "OK"

@app.route("/", methods=["POST"])
def noa_proxy():
    log, t0 = app.logger, time.time()
    log.info("=== New request ===")

    audio = request.files.get("audio")
    if not audio:
        return jsonify(error="No audio"), 400

    # --- 一時保存（拡張子維持して Whisper へ直送） ---------------------
    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as fp:
        audio.save(fp.name)

    # --- Whisper ----------------------------------------------------------
    tr0 = time.time()
    with open(fp.name, "rb") as f:
        text = client.audio.transcriptions.create(
            model=FAST_WHISPER, file=f, response_format="text", temperature=0
        )
    log.info("Transcript (%.2fs): %s", time.time()-tr0, text[:80])

    # --- Chat -------------------------------------------------------------
    messages = [{"role": "user", "content": text}]
    ch0 = time.time()
    chat = client.chat.completions.create(
        model=CHAT_MODEL, messages=messages
    )
    answer = chat.choices[0].message.content.strip()
    log.info("Answer (%.2fs): %s", time.time()-ch0, answer[:80])

    # --- Response ---------------------------------------------------------
    body = {
        "reply":          answer,
        "display_text":   answer[:60],  # HUD用に短縮
        "reply_audio":    "",           # nullより空文字
        "topic_changed":  False
    }
    log.info("Total time %.2fs — returning JSON", time.time()-t0)
    return jsonify(body), 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.getenv("PORT", 10000)))
