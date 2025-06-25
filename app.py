# requirements: flask, openai, python-dotenv (for loading API key from .env)
from flask import Flask, request, jsonify
import openai, os

openai.api_key = os.getenv("OPENAI_API_KEY")  # 環境変数にOpenAI APIキーを設定しておく

app = Flask(__name__)

@app.route("/", methods=["POST"])
def chatgpt_proxy():
    # Noaアプリから送信された音声ファイルとフォームデータを取得
    audio_file = request.files.get("audio")
    if audio_file is None:
        return "No audio file provided", 400
    # 必要なら履歴やシステムプロンプトも取得
    system_prompt = request.form.get("noa_system_prompt", "")  # Noaのシステムプロンプト
    messages_json = request.form.get("messages")  # 過去のメッセージ履歴(JSON文字列)
    # Whisper APIで音声 -> テキスト変換
    try:
        transcript = openai.Audio.transcribe("whisper-1", audio_file)
    except Exception as e:
        return f"Whisper API error: {e}", 500
    user_text = transcript["text"] if isinstance(transcript, dict) and "text" in transcript else transcript

    # ChatGPTへのメッセージ構築
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    if messages_json:
        try:
            import json
            history = json.loads(messages_json)
            # 履歴は NoaMessage オブジェクトのリスト。roleとcontentを持つ想定で取り出す
            for msg in history:
                if msg.get("role") and msg.get("content"):
                    messages.append({"role": msg["role"], "content": msg["content"]})
        except json.JSONDecodeError:
            pass
    # 最後に今回のユーザー発話を追加
    messages.append({"role": "user", "content": user_text})

    # ChatGPT (GPT-4) API呼び出し
    try:
        chat_response = openai.ChatCompletion.create(model="gpt-4", messages=messages)
    except Exception as e:
        return f"OpenAI API error: {e}", 500
    # 回答テキストを取得
    answer_text = chat_response["choices"][0]["message"]["content"]

    # 必要なら音声合成（TTS）がオンかを確認し、フラグを含める（ここでは省略）

    # JSON形式で応答（回答テキストを返す）
    return jsonify({"reply": answer_text})
