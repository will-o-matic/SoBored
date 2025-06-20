# SoBored App

A smart event aggregator and assistant that helps surface interesting things to do in your city. It pulls event data from multiple input channels (flyers, URLs, text, etc.), extracts structured event info, and saves it to a Notion database for exploration and querying.

---

## 🚀 Getting Started (Telegram Bot + FastAPI + LangGraph + ngrok)

This project sets up a Telegram bot that receives user messages, classifies the content (text, image, or URL), and replies with the classification. It uses:

- **FastAPI** to handle Telegram webhooks
- **LangGraph** to classify content type
- **ngrok** to expose your local server during development
- **python-dotenv** to securely manage secrets

---

### 🔧 Prerequisites

- Python 3.9+
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- `ngrok` installed (`brew install ngrok`, `choco install ngrok`, or download from https://ngrok.com)

---

### 📦 Install Dependencies

Create a virtual environment and install required packages:

```bash
pip install -r requirements.txt
```

Create a .env file at the project root with:

TELEGRAM_BOT_TOKEN=your-telegram-token-here

Make sure .env is listed in .gitignore to avoid committing secrets.

Start the local webhook server on port 8000:

uvicorn telegram-bot.main:app --reload --port 8000

In a separate terminal:

ngrok http 8000

Copy the HTTPS forwarding URL (e.g. https://abc123.ngrok.io).

Set your webhook using your bot token and ngrok URL:

https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://abc123.ngrok.io/telegram/webhook

Replace:

    <YOUR_BOT_TOKEN> with your real token

    https://abc123.ngrok.io with your actual ngrok URL

A successful response will look like:

{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}

🧪 Test It!

Send your bot a message:

    Text → it should reply “Classified as: text”

    A URL → reply: “Classified as: url”

    An image → reply: “Classified as: image”

You should see FastAPI and ngrok logs updating as requests come in.

## Tech Stack

| Layer | Technology |
|-------|------------|
| Chat Interface | Telegram Bot (MVP), Web UI (Future) |
| Orchestration | [LangGraph](https://github.com/langchain-ai/langgraph) |
| Parsing / NLP | [LangChain](https://www.langchain.com/) tools + custom logic |
| Event Storage | Notion database via API (MCP optional later) |
| Deployment | Vercel (API endpoints + front-end) |

---

## MVP Features

- Users can send **text, images, or URLs** to the Telegram bot.
- System parses event info (title, date, location, etc.) from the input.
- Structured event data is saved to a **Notion database**.
- Bot replies with a confirmation (or error handling if info is missing).

---

## Architecture Overview

### Interfaces Layer
- **Telegram Bot**: Receives user messages and sends them to a LangGraph processing pipeline.
- (Future) **Web-based Chat UI** via Next.js + Vercel
- (Optional) **Discord bot**, Email input, or Instagram scraping

### LangGraph Processing Flow

```text
Input → Classify →
  → Image → OCR → Parse → Validate
  → Text → Parse → Validate
  → URL → Scrape → Parse → Validate
→ Deduplicate
→ Enrich (if needed)
→ Save to Notion
→ Respond to user
````

Each step is a LangGraph node (LangChain tools, custom code, or API call). All steps work on a shared `event_state` object that accumulates metadata.

### Notion DB Schema (MVP)

| Field          | Type         |
| -------------- | ------------ |
| Title          | Text         |
| Date/Time      | Date         |
| Location       | Text         |
| Description    | Rich Text    |
| Source         | URL / Text   |
| Tags           | Multi-select |
| Hydrated       | Checkbox     |
| Original Input | File / Text  |
| Confidence     | Number       |

---

## Future Expansion Plan

### Enrichment via LangGraph

* Hydrate missing fields by scraping source URLs or using APIs (e.g., Google Maps for venue resolution).
* Geotag events for map-based UI later.

### Notion Monitoring

* **Pull-based:** Cron job checks for new rows (`hydrated = false`) and enriches them.
* **Push-based:** (When supported) Use Notion webhooks or MCP to trigger enrichment pipelines on update.

### Additional Input Sources

* Web crawling for known venues
* Email newsletter parsing (via forwarding)
* Instagram post parsing (caption + image OCR)

### Front-End Plans

* Build a **Next.js web app** to:

  * Browse and filter events
  * Upload flyers or links
  * Explore events via calendar or map views

---

## Example User Interactions

| Input                                   | Behavior                                               |
| --------------------------------------- | ------------------------------------------------------ |
| Flyer image                             | OCR → parse → save → reply: "Added *Live Jazz at 8pm*" |
| Text: "Art show at Dolores Park on Sat" | NLP → save → reply with confirmation                   |
| URL                                     | Scrape → parse → validate → save                       |

---

## Roadmap

* [ ] Telegram MVP working end-to-end
* [ ] Cron-based Notion hydrator
* [ ] Add enrichment: venue details, map links
* [ ] Web UI with calendar + filters
* [ ] Add email/Instagram input support

---

