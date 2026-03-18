---
title: Instagram AI Boost Agent
emoji: 🚀
colorFrom: purple
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# Instagram AI Boost Agent

AI-powered Instagram post analyzer and organic growth tool. Paste a post URL or @username, and get optimized hashtags, engagement strategies, and content tips powered by Groq AI.

## Features

- **Smart Hashtag Generation** -- 3 optimized sets (Maximum Reach, Niche Targeted, Low Competition) following 2026 Instagram algorithm best practices
- **Content Analysis** -- AI vision + text analysis to understand your post's category, mood, audience, and themes
- **Organic Boost Strategy** -- Best posting times, caption rewrites, first-comment suggestions, engagement hooks
- **Community Actions** -- Specific pre-posting engagement tasks for your niche
- **Follow-Up Ideas** -- Related content ideas to maintain momentum
- **Image Auto-Tagging** -- Uses AI Auto Tagging API for image-based tag suggestions
- **Fallback Manual Input** -- Works even without direct Instagram access via caption + image upload

## Quick Start

### 1. Get a free Groq API key

Go to [Groq Console](https://console.groq.com/keys) and create a free API key (takes 30 seconds).

### 2. Set up the project

```bash
cd instagram-boost-agent

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure your API key

```bash
cp .env.example .env
```

Edit `.env` and paste your Groq API key:

```
GROQ_API_KEY=your_key_here
```

### 4. Run the app

```bash
source venv/bin/activate   # if not already activated
uvicorn app.main:app --reload --port 8000
```

Open [http://localhost:8000](http://localhost:8000) in your browser.

## Usage

### Option A: Post URL or @Username
Paste an Instagram post URL (e.g. `https://www.instagram.com/p/ABC123/`) or a username (e.g. `@natgeo`) into the input field and click **Analyze**.

### Option B: Manual Input
If Instagram data extraction is rate-limited, use the manual input section:
1. Paste your caption or describe your content
2. Optionally drag & drop an image for visual analysis
3. Click **Analyze**

## Tech Stack

- **Backend**: FastAPI (Python)
- **Frontend**: Jinja2 + Tailwind CSS
- **AI**: Groq (Llama 3.3 70B for text, Llama 3.2 11B Vision for images) -- free tier with generous limits
- **Instagram Data**: instaloader (public post extraction)
- **Image Tags**: AI Auto Tagging API (free, no key needed)

## Project Structure

```
instagram-boost-agent/
  app/
    main.py                # FastAPI routes
    services/
      instagram.py         # Instagram data extraction
      ai_engine.py         # Groq AI integration
      hashtag_service.py   # Hashtag generation pipeline
      boost_strategy.py    # Organic boost recommendations
    templates/
      index.html           # Web UI
    static/
      style.css            # Custom styles
  requirements.txt
  .env.example
  README.md
```

## Limitations

- Instaloader may be rate-limited by Instagram for heavy use. The manual input mode always works as a fallback.
- Trending data is AI-generated, not a live Instagram feed.
- This tool provides recommendations -- actual results depend on content quality and account history.
- Free Groq API tier allows 30 requests per minute and 14,400 per day.
