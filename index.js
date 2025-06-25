const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

app.post('/chat', async (req, res) => {
  try {
    const prompt = req.body.prompt; // Noaアプリから送られるプロンプト

    const response = await axios.post('https://api.openai.com/v1/chat/completions', {
      model: 'gpt-4o', // ここでモデルを指定（gpt-4でも可）
      messages: [
        { role: 'system', content: "You are Noa, a smart and witty personal AI assistant inside the user's AR smart glasses that answers all user queries and questions" },
        { role: 'user', content: prompt }
      ],
      max_tokens: 300,
      temperature: 0.3
    }, {
      headers: { 'Authorization': `Bearer ${process.env.OPENAI_API_KEY}` } // ← 環境変数に修正
    });

    res.json(response.data);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'サーバでエラーが発生しました。' });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`サーバ起動中: ポート${port}`));
