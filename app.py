from flask import Flask, request, jsonify
import openai, os, json, tempfile

openai.api_key = os.getenv("OPENAI_API_KEY")

app = Flask(__name__)

@app.route("/", methods=["GET"])
def index():
    return "Server is up and running!"

@app.route("/", methods=["POST"])
def chatgpt_proxy():
    app.logger.info("Received POST request")
    
    audio_file = request.files.get("audio")
    if audio_file is None:
        app.logger.error("No audio file provided")
        return jsonify({"error": "No audio file provided"}), 400

    system_prompt = request.form.get("noa_system_prompt", "")
    messages_json = request.form.get("messages", "[]")

    app.logger.info(f"System Prompt: {system_prompt}")
    app.logger.info(f"Messages JSON: {messages_json}")

    # Whisper用に一時ファイルとして音声を保存
    try:
        with tempfile.NamedTemporaryFile(suffix=".wav") as temp_audio:
            audio_file.save(temp_audio.name)
            temp_audio.seek(0)
            
            # openai==0.28を使用しているため、この形式で呼び出す
            transcript = openai.Audio.transcribe(
                model="whisper-1",
                file=open(temp_audio.name, "rb")
            )
        user_text = transcript["text"] if isinstance(transcript, dict) else transcript
        app.logger.info(f"Whisper transcript: {user_text}")
    except Exception as e:
        app.logger.exception(f"Whisper API error: {e}")
        return jsonify({"error": f"Whisper API error: {str(e)}"}), 500

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

    # ChatGPTにリクエストを送信
    try:
        chat_response = openai.ChatCompletion.create(model="gpt-4o", messages=messages)
        answer_text = chat_response["choices"][0]["message"]["content"]
        app.logger.info(f"ChatGPT response: {answer_text}")
    except Exception as e:
        app.logger.exception(f"OpenAI API error: {e}")
        return jsonify({"error": f"OpenAI API error: {str(e)}"}), 500

    # Noaアプリに適したレスポンスを返す
    response = {
        "reply": answer_text,
        "topic_changed": False,
        "display_text": answer_text,
        "reply_audio": None
    }

    return jsonify(response)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port, debug=True)
