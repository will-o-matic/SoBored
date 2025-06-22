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
- A Notion integration and database (see Notion Setup below)
- `ngrok` installed:
  - **macOS**: `brew install ngrok`
  - **Windows**: `choco install ngrok` or download from https://ngrok.com
  - **WSL/Linux**: See installation instructions in the WSL setup section below

### 🪟 VS Code + WSL Setup (Windows Users)

For the best development experience on Windows, use VS Code with the Remote-WSL extension to work directly in the WSL filesystem.

#### Initial Setup
1. **Install Prerequisites:**
   - [VS Code](https://code.visualstudio.com/)
   - [Remote - WSL extension](https://marketplace.visualstudio.com/items?itemName=ms-vscode-remote.remote-wsl)
   - [Windows Subsystem for Linux](https://docs.microsoft.com/en-us/windows/wsl/install)

2. **Clone Project to WSL Filesystem:**
   ```bash
   # In WSL terminal, clone to your home directory for better performance
   cd ~
   git clone https://github.com/your-username/SoBored.git
   cd SoBored
   ```

3. **Open in VS Code:**
   ```bash
   # From WSL terminal in the project directory
   code .
   ```
   This will open VS Code in Remote-WSL mode with the project loaded.


#### Install ngrok in WSL
```bash
# Install ngrok directly in WSL
curl -s https://ngrok-agent.s3.amazonaws.com/ngrok.asc | sudo tee /etc/apt/trusted.gpg.d/ngrok.asc >/dev/null
echo "deb https://ngrok-agent.s3.amazonaws.com buster main" | sudo tee /etc/apt/sources.list.d/ngrok.list
sudo apt update && sudo apt install ngrok

# Or download manually:
wget https://bin.equinox.io/c/bNyj1mQVY4c/ngrok-v3-stable-linux-amd64.tgz
tar xvzf ngrok-v3-stable-linux-amd64.tgz
sudo mv ngrok /usr/local/bin
```

#### VS Code Remote-WSL Benefits
- **Seamless file editing**: Edit files directly in WSL filesystem
- **Integrated terminal**: VS Code terminal runs in WSL context
- **Extension support**: Install Python extensions that work with WSL
- **Git integration**: Works natively with WSL git
- **Debugging**: Full debugging support for Python apps

#### Access from Windows File Explorer
You can still access your WSL project files from Windows at:
```
\\wsl$\Ubuntu\home\yourusername\SoBored
```

#### Claude Code Usage
When using Claude Code CLI:
```bash
# In WSL terminal, navigate to project
cd ~/SoBored
# Claude Code will work seamlessly with files in WSL filesystem
```

**Why This Setup Works Better:**
- Faster file operations (no Windows/WSL filesystem bridge)
- Better permissions handling
- Native Linux tooling performance
- Seamless integration between VS Code and WSL

---

### 🗃️ Notion Setup

1. Create a Notion integration at https://www.notion.com/my-integrations
2. Copy the integration token (you'll add this to `.env` in the next step)
3. Create or select a Notion page where you want your events database
4. Share the page with your integration (Share → Add connections)

### 📦 Install Dependencies & Configuration

Set up your Python environment and install required packages:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a .env file at the project root with:

```
TELEGRAM_BOT_TOKEN=your-telegram-token-here
NOTION_TOKEN=your-notion-integration-token-here
NOTION_DATABASE_ID=your-notion-database-id-here
```

Make sure .env is listed in .gitignore to avoid committing secrets.

Complete the Notion database setup:
```bash
python test_run_graph.py
```
Follow the prompts to create your events database and copy the database ID to your `.env` file as `NOTION_DATABASE_ID`.

### 🚀 Running the Application

Start the local webhook server on port 8000:

```bash
uvicorn telegram-bot.main:app --reload --port 8000
```

In a separate terminal, expose with ngrok:

```bash
ngrok http 8000
```

Copy the HTTPS forwarding URL (e.g. https://abc123.ngrok.io).

Set your webhook using your bot token and ngrok URL:

```
https://api.telegram.org/bot<YOUR_BOT_TOKEN>/setWebhook?url=https://abc123.ngrok.io/telegram/webhook
```

Replace:
- `<YOUR_BOT_TOKEN>` with your real token
- `https://abc123.ngrok.io` with your actual ngrok URL

A successful response will look like:
```json
{
  "ok": true,
  "result": true,
  "description": "Webhook was set"
}
```

### 🧪 Testing

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

### Notion DB Schema (Implemented)

| Field          | Type         | Description |
| -------------- | ------------ | ----------- |
| Title          | Title        | Event name or generated title |
| Date/Time      | Date         | Event date/time |
| Location       | Rich Text    | Event location/venue |
| Description    | Rich Text    | Event description or raw input |
| Source         | Select       | Input source (telegram, web, email, instagram) |
| URL            | URL          | Link if input was a URL |
| Classification | Select       | Input type (event, url, text, image, unknown) |
| Status         | Select       | Processing status (new, processed, archived) |

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
  - Ability to intake text, photo, and URL
  - Parse and hydrate based on available context
  - Save to Notion
* [ ] Cron-based Notion hydrator
* [ ] Add enrichment: venue details, map links
* [ ] Web UI with calendar + filters
* [ ] Add email/Instagram input support

---

