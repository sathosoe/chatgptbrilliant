const express = require("express");
const axios = require("axios");
const cors = require("cors");
require('dotenv').config();

const app = express();
app.use(express.json());
app.use(cors());

// OpenAI APIキーを設定（Render.comの環境変数に設定済み）
const OPENAI_API_KEY = process.env.OPENAI_API_KEY;

app.post("/chat", async (req, res) => {
  const userPrompt = req.body.prompt;

  try {
    const response = await axios.post(
      "https://api.openai.com/v1/chat/completions",
      {
        model: "gpt-4o",
        messages: [
          {
            role: "system",
            content: "あなたはスマートグラス内のAIアシスタントNoaです。",
          },
          {
            role: "user",
            content: userPrompt,
          },
        ],
        max_tokens: 300,
        temperature: 0.3,
      },
      {
        headers: {
          "Authorization": `Bearer ${OPENAI_API_KEY}`,
          "Content-Type": "application/json",
        },
      }
    );

    // Noaが想定する形式に合わせる
    res.json({
      topic_changed: false,
      content: response.data.choices[0].message.content
    });

  } catch (error) {
    console.error("Error:", error.response ? error.response.data : error.message);
    res.status(500).json({
      topic_changed: false,
      content: "申し訳ありません。エラーが発生しました。"
    });
  }
});

// サーバの起動ポートを環境変数または10000で指定
const PORT = process.env.PORT || 10000;

app.listen(PORT, () => {
  console.log(`サーバが起動しました。ポート番号: ${PORT}`);
});
