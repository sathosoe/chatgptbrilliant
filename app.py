from flask import Flask, request, jsonify
import openai
import os
import json
import tempfile
import subprocess

openai.api_key = os.getenv("OPENAI_API_KEY")
app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Server is up and running!"

@app.route("/", methods=["POST"])
def chatgpt_proxy():
    app.logger.info("=== New request received ===")
    audio_file = request.files.get("audio")
    if audio_file is None:
        app.logger.error("No audio file provided")
        return jsonify({"error": "No audio file provided"}), 400

    system_prompt = request.form.get("noa_system_prompt", "")
    messages_json = request.form.get("messages", "[]")
    app.logger.info(f"System prompt: {system_prompt}")
    app.logger.info(f"messages_json: {messages_json}")

    src = dst = None
    try:
        # 一時ファイルへ保存
        src = tempfile.NamedTemporaryFile(delete=False, suffix=".input")
        audio_file.save(src.name)
        src.close()
        app.logger.info(f"Audio saved to temp file: {src.name}")

        dst = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        dst.close()
        app.logger.info(f"Preparing converted file: {dst.name}")

        # ffmpeg変換
        ffmpeg_cmd = [
            "ffmpeg", "-y",
            "-i", src.name,
            "-ar", "16000",
            "-ac", "1",
            dst.name
        ]
        app.logger.info(f"Running ffmpeg command: {' '.join(ffmpeg_cmd)}")
        subprocess.run(ffmpeg_cmd, check=True)
        app.logger.info(f"ffmpeg conversion complete: {dst.name}")

        # Whisper文字起こし
        with open(dst.name, "rb") as converted_audio:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=converted_audio,
                response_format="text"
            )
        user_text = transcript
        app.logger.info(f"Whisper transcript: {user_text}")

    except Exception as e:
        app.logger.exception(f"Whisper API or ffmpeg error: {e}")
        return jsonify({"error": f"Whisper API error: {str(e)}"}), 500
    finally:
        # cleanup
        try:
            if src: os.unlink(src.name)
            if dst: os.unlink(dst.name)
            app.logger.info("Temp files cleaned up.")
        except Exception as cleanup_e:
            app.logger.error(f"Cleanup error: {cleanup_e}")

    # ChatGPTへのメッセージ作成
    messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    try:
        history = json.loads(messages_json)
        for msg in history:
            if msg.get("role") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
        app.logger.info(f"ChatGPT messages history: {messages}")
    except json.JSONDecodeError as e:
        app.logger.exception(f"JSON decode error: {e}")
        return jsonify({"error": "Invalid JSON in messages"}), 400

    messages.append({"role": "user", "content": user_text})
    app.logger.info(f"Final messages to ChatGPT: {messages}")

    try:
        chat_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        answer_text = chat_response.choices[0].message.content
        app.logger.info(f"ChatGPT response: {answer_text}")
    except Exception as e:
        app.logger.exception(f"OpenAI API error: {e}")
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

    app.logger.info("Returning response to Noa/Frame.")
    return jsonify({
        "reply": answer_text,
        "display_text": answer_text,
        "reply_audio": None,
        "topic_changed": False
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
