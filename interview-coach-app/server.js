const express = require('express');
const cors = require('cors');
require('dotenv').config();
const { Anthropic } = require('@anthropic-ai/sdk');

const app = express();
const PORT = process.env.PORT || 5000;

app.use(cors());
app.use(express.json());
app.use(express.static('public'));

const client = new Anthropic({
  apiKey: process.env.CLAUDE_API_KEY
});

app.post('/api/generate-question', async (req, res) => {
  try {
    const { topic, difficulty } = req.body;

    if (!topic || !difficulty) {
      return res.status(400).json({ error: 'Topic and difficulty are required' });
    }

    const message = await client.messages.create({
      model: 'claude-opus-4-7',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: `Generate a ${difficulty} level Data Structures and Algorithms problem on the topic: ${topic}.

Format the response as:
PROBLEM TITLE: [title]
DIFFICULTY: ${difficulty}
TOPIC: ${topic}

PROBLEM STATEMENT:
[detailed problem description]

CONSTRAINTS:
[list constraints]

EXAMPLE:
[provide input/output example]

FOLLOW-UP QUESTIONS:
[3-4 follow-up questions to think about]`
        }
      ]
    });

    const problem = message.content[0].text;
    res.json({ problem });
  } catch (error) {
    console.error('Error generating question:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/get-hint', async (req, res) => {
  try {
    const { question, stuckPoint } = req.body;

    if (!question || !stuckPoint) {
      return res.status(400).json({ error: 'Question and stuckPoint are required' });
    }

    const message = await client.messages.create({
      model: 'claude-opus-4-7',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: `Given this DSA problem:
"${question}"

The student is stuck at: "${stuckPoint}"

Provide helpful hints WITHOUT revealing the complete solution. Include:
1. Key insight or approach to consider
2. Data structure or algorithm hint
3. A specific question to guide them
4. One small code snippet example (if helpful)

Make it educational and guide them to figure it out themselves.`
        }
      ]
    });

    const hint = message.content[0].text;
    res.json({ hint });
  } catch (error) {
    console.error('Error getting hint:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/evaluate-answer', async (req, res) => {
  try {
    const { question, answer } = req.body;

    if (!question || !answer) {
      return res.status(400).json({ error: 'Question and answer are required' });
    }

    const message = await client.messages.create({
      model: 'claude-opus-4-7',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: `Evaluate this DSA solution:

PROBLEM:
"${question}"

STUDENT'S ANSWER/APPROACH:
"${answer}"

Provide:
1. Correctness assessment (Correct/Partially Correct/Incorrect)
2. Time & Space Complexity analysis
3. What's good about the approach
4. What could be improved
5. Edge cases they might have missed
6. 2-3 suggestions for better solution`
        }
      ]
    });

    const evaluation = message.content[0].text;
    res.json({ evaluation });
  } catch (error) {
    console.error('Error evaluating answer:', error);
    res.status(500).json({ error: error.message });
  }
});

app.post('/api/chat', async (req, res) => {
  try {
    const { message } = req.body;

    if (!message) {
      return res.status(400).json({ error: 'Message is required' });
    }

    const response = await client.messages.create({
      model: 'claude-opus-4-7',
      max_tokens: 1024,
      messages: [
        {
          role: 'user',
          content: `You are a DSA (Data Structures and Algorithms) tutor helping Scaler students.
User query: "${message}"

Respond helpfully. If it's about DSA:
- Generate problems
- Provide hints
- Evaluate solutions
- Explain concepts

Keep responses concise and educational.`
        }
      ]
    });

    const reply = response.content[0].text;
    res.json({ reply });
  } catch (error) {
    console.error('Error in chat:', error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(PORT, () => {
  console.log(`✅ Interview Coach running at http://localhost:${PORT}`);
  console.log(`🌐 Open your browser to http://localhost:${PORT}`);
});
