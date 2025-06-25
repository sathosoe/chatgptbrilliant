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
    audio_file = request.files.get("audio")
    if audio_file is None:
        return jsonify({"error": "No audio file provided"}), 400

    system_prompt = request.form.get("noa_system_prompt", "")
    messages_json = request.form.get("messages", "[]")

    src = dst = None
    try:
        # 一時ファイルへ保存
        src = tempfile.NamedTemporaryFile(delete=False, suffix=".input")
        audio_file.save(src.name)
        src.close()

        dst = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        dst.close()

        # ffmpeg変換
        subprocess.run([
            "ffmpeg", "-y",
            "-i", src.name,
            "-ar", "16000",
            "-ac", "1",
            dst.name
        ], check=True)

        # Whisper文字起こし
        with open(dst.name, "rb") as converted_audio:
            transcript = openai.audio.transcriptions.create(
                model="whisper-1",
                file=converted_audio,
                response_format="text"
            )
        user_text = transcript
    except Exception as e:
        return jsonify({"error": f"Whisper API error: {str(e)}"}), 500
    finally:
        # cleanup
        try:
            if src: os.unlink(src.name)
            if dst: os.unlink(dst.name)
        except Exception:
            pass

    # ChatGPTへのメッセージ作成
    messages = [{"role": "system", "content": system_prompt}] if system_prompt else []
    try:
        history = json.loads(messages_json)
        for msg in history:
            if msg.get("role") and msg.get("content"):
                messages.append({"role": msg["role"], "content": msg["content"]})
    except json.JSONDecodeError as e:
        return jsonify({"error": "Invalid JSON in messages"}), 400

    messages.append({"role": "user", "content": user_text})

    try:
        chat_response = openai.chat.completions.create(
            model="gpt-4o",
            messages=messages
        )
        answer_text = chat_response.choices[0].message.content
    except Exception as e:
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

    return jsonify({
        "reply": answer_text,
        "display_text": answer_text,
        "reply_audio": None,
        "topic_changed": False
    })

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
