# LoopLAB — Instagram AI Assistant

AI-powered Instagram content tools built into the LoopLAB social media platform.

## Features

- **Caption Generator** — Write engaging captions with customizable tone and length
- **Hashtag Generator** — Get relevant hashtag suggestions for any post topic
- **Bio Generator** — Craft a compelling Instagram bio in seconds
- **Content Ideas** — Brainstorm post and Reel ideas for your niche

## Setup

1. Install dependencies:

```bash
npm install
```

2. Configure your OpenAI API key:

```bash
cp .env.example .env
# Edit .env and set OPENAI_API_KEY=sk-...
```

3. Start the server:

```bash
npm start
```

4. Open [http://localhost:3000/instagram-ai.html](http://localhost:3000/instagram-ai.html)

## Tech Stack

- **Frontend**: Bootstrap 4, jQuery
- **Backend**: Node.js + Express
- **AI**: OpenAI GPT-4o-mini

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Check server and AI configuration status |
| POST | `/api/generate/caption` | Generate an Instagram caption |
| POST | `/api/generate/hashtags` | Generate hashtag suggestions |
| POST | `/api/generate/bio` | Generate an Instagram bio |
| POST | `/api/generate/ideas` | Generate content ideas |

## Notes

- This tool generates content only — it does not post to Instagram directly.
- To publish via API, you would need a [Meta Developer App](https://developers.facebook.com/) with Instagram Graph API access.
