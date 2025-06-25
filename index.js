const express = require('express');
const axios = require('axios');

const app = express();
app.use(express.json());

app.post('/chat', async (req, res) => {
  try {
    const prompt = req.body.prompt; // Noaアプリから送られるプロンプト

    const response = await axios.post('https://api.openai.com/v1/chat/completions', {
      model: 'gpt-4-vision-preview', // ここでモデルを指定（gpt-4でも可）
      messages: [
        { role: 'system', content: 'あなたはARグラスのNoaです。簡潔に日本語で答えてください。' },
        { role: 'user', content: prompt }
      ],
      max_tokens: 300,
      temperature: 0.3
    }, {
      headers: { 'Authorization': `Bearer ${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
}` }
    });

    res.json(response.data);
  } catch (error) {
    console.error(error);
    res.status(500).json({ error: 'サーバでエラーが発生しました。' });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`サーバ起動中: ポート${port}`));
