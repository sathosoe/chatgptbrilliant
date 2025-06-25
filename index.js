const express = require('express');
const axios = require('axios');
const app = express();
app.use(express.json());

app.post('/chat', async (req, res) => {
  try {
    const prompt = req.body.prompt;

    const response = await axios.post('https://api.openai.com/v1/chat/completions', {
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: "You are Noa, a smart and witty personal AI assistant inside the user's AR smart glasses that answers all user queries and questions." },
        { role: 'user', content: prompt }
      ],
      max_tokens: 300,
      temperature: 0.3
    }, {
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    res.json(response.data);
  } catch (error) {
    console.error('Error:', error.response ? error.response.data : error.message);
    res.status(500).json({ error: error.message });
  }
});

const port = process.env.PORT || 3000;
app.listen(port, () => console.log(`サーバ起動中: ポート${port}`));
