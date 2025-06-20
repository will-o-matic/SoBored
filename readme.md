# SoBored App

A smart event aggregator and assistant that helps surface interesting things to do in your city. It pulls event data from multiple input channels (flyers, URLs, text, etc.), extracts structured event info, and saves it to a Notion database for exploration and querying.

---



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

