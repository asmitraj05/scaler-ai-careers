# Scaler Interview Coach - DSA Problem Generator

A web-based platform for Scaler students to practice DSA problems with AI-powered hints, problem generation, and solution evaluation.

## Features

✨ **Generate DSA Problems** - Get problems based on topic and difficulty level
💡 **Smart Hints** - Get guidance without revealing solutions
✅ **Solution Evaluation** - Get feedback on your code approach
💬 **Chat Interface** - Ask any DSA-related questions
📚 **Multiple Topics** - Trees, Arrays, LinkedLists, Graphs, DP, Binary Search, Strings, Hashing

## Setup Instructions

### Step 1: Get a Claude API Key

1. Go to https://console.anthropic.com/
2. Sign up or log in
3. Click "API Keys" in the left sidebar
4. Create a new API key
5. Copy the key (you'll need it in Step 3)

### Step 2: Navigate to Project Directory

```bash
cd /Users/asmitraj/Desktop/CLAUDE\ PROJECT/interview-coach-app
```

### Step 3: Create `.env` File

Create a file named `.env` in the project root with:

```
CLAUDE_API_KEY=your_api_key_here
PORT=5000
```

Replace `your_api_key_here` with your actual Claude API key from Step 1.

### Step 4: Install Dependencies

```bash
npm install
```

This will install:
- express (web framework)
- cors (cross-origin requests)
- dotenv (environment variables)
- @anthropic-ai/sdk (Claude API)

### Step 5: Start the Server

```bash
npm start
```

You should see:
```
✅ Interview Coach running at http://localhost:5000
🌐 Open your browser to http://localhost:5000
```

### Step 6: Open in Browser

Click this link or paste in your browser:
👉 **http://localhost:5000**

## How to Use

### Generate a Problem
1. Click **"➕ Generate Problem"** button
2. Enter a topic (e.g., "Trees")
3. Select difficulty (Easy/Medium/Hard)
4. Click **"Generate Problem"**

### Get a Hint
1. Click **"💡 Get Hint"** button
2. Paste the problem statement
3. Describe where you're stuck
4. Click **"Get Hint"**

### Evaluate Your Answer
1. Click **"✅ Evaluate Answer"** button
2. Paste the problem
3. Paste your solution/approach
4. Click **"Evaluate"**

### Quick Topic Buttons
- Click any topic button (Trees, Arrays, etc.) to quickly generate problems
- Select difficulty first, then click the topic

## Troubleshooting

### Issue: "API key not found" error
- Make sure you created the `.env` file correctly
- Verify your Claude API key is valid
- Restart the server after creating/editing `.env`

### Issue: "Cannot connect to server"
- Make sure the server is running (`npm start`)
- Check that port 5000 is not in use
- Try a different port: `PORT=3000 npm start`

### Issue: No response from AI
- Check your Claude API key has credits
- Ensure internet connection is working
- Try refreshing the page

## File Structure

```
interview-coach-app/
├── server.js           # Backend server
├── package.json        # Dependencies
├── .env               # API keys (create this)
├── .env.example       # Example env file
└── public/
    ├── index.html     # Frontend UI
    ├── style.css      # Styling
    └── script.js      # Frontend logic
```

## API Endpoints

### POST /api/chat
Send any DSA question to the AI.

### POST /api/generate-question
Generate a DSA problem by topic and difficulty.

### POST /api/get-hint
Get hints for a problem without revealing the solution.

### POST /api/evaluate-answer
Get feedback on your solution.

## Sharing with Students

### For Local Use:
Share the project folder and these instructions.

### For Production (Optional):
Deploy to:
- **Vercel** - `vercel deploy`
- **Heroku** - `heroku create` then `git push heroku main`
- **Your own server** - Use `pm2` to keep it running

## Support

If you encounter issues:
1. Check the troubleshooting section above
2. Make sure Node.js is installed: `node --version`
3. Verify all dependencies: `npm ls`
4. Restart the server

Enjoy learning DSA! 🚀
