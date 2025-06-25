const express = require('express');
const axios = require('axios');
const cors = require('cors');
require('dotenv').config();

const app = express();
const port = process.env.PORT || 3000;

app.use(express.json());
app.use(cors());

app.post('/chat', async (req, res) => {
  try {
    const userPrompt = req.body.prompt || req.body.messages?.[0]?.content;
    
    if (!userPrompt) {
      return res.status(400).json({ error: 'Prompt is missing or null.' });
    }

    const openAIResponse = await axios.post('https://api.openai.com/v1/chat/completions', {
      model: 'gpt-4o',
      messages: [
        { role: 'system', content: 'You are Noa, a smart and witty personal AI assistant inside the user\'s AR smart glasses that answers all user queries and questions.' },
        { role: 'user', content: userPrompt }
      ],
      max_tokens: 300,
      temperature: 0.3
    }, {
      headers: {
        'Authorization': `Bearer ${process.env.OPENAI_API_KEY}`,
        'Content-Type': 'application/json'
      }
    });

    res.json({
      reply: openAIResponse.data.choices[0].message.content
    });

  } catch (error) {
    console.error('OpenAI API Error:', error.response ? error.response.data : error.message);
    res.status(500).json({ error: 'Internal Server Error' });
  }
});

app.listen(port, () => {
  console.log(`Server is running on port ${port}`);
});
