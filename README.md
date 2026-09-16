# «Тренды и Бренды» Autoposter

A rule-based Telegram autoposter that selects notable brand moves, consumer
trends, retail innovations, campaigns, collaborations, and rebrands in Russia
and around the world. Local execution remains safe by default.

## What it includes

- RSS, declarative HTML, and local static collectors.
- A shared `news_item` data shape.
- Date filtering, project-owned relevance, scoring, and stable ranking.
- URL, title, and conservative cross-source event deduplication.
- Generic article text and `og:image` / `twitter:image` extraction.
- Isolated source-specific article extractors and stop markers.
- Telegram text/photo publishing with temporary-file fallback.
- Native eight-second MP4 cards for the 15:00 and 19:00 publication slots.
- Optional licensed Pexels motion backgrounds with creator attribution.
- Duplicate protection for uncertain Telegram network outcomes.
- JSON publication history with backward-compatible fingerprints.
- Safe `DRY_RUN=True`, a local process lock, tests, and GitHub Actions.

No paid API, AI service, database, browser automation, or framework is needed.

## Architecture

```text
reusable infrastructure             channel-specific behavior
core/ collectors/ processing/       project/sources.py
article/ generation/ publishing/ +  project/filters.py
storage/                             project/scoring.py
                                     project/formatter.py
                                     project/settings.py
```

`main.py` composes these two layers with ordinary Python functions. There is no
plugin framework or dependency-injection container.

## Quick start

```bash
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
cp .env.example .env
.venv/bin/python -m pytest
.venv/bin/python main.py
```

The project combines direct Russian industry RSS feeds with narrow Google News
RSS searches for international coverage. Relevance, event categories, scoring,
and Telegram presentation live in `project/`.

## Channel behavior

- Direct coverage: Postium collaborations, AdIndex, New Retail, and Retail.ru.
- Discovery feeds target famous consumer, technology, entertainment, food, and
  fashion brands. Google News items are accepted only from trusted publishers.
- A recognizable brand and a concrete launch, collaboration, campaign,
  rebrand, meme, controversy, or other viral event are both required.
- Routine appointments, market research, events, roundups, how-to articles,
  financial reports, and workforce news are excluded before scoring.
- Posts contain a headline, no more than two factual sentences, a short closing
  reaction, and a compact dated footer with the channel rubric, source link,
  and one category hashtag.
- Article imagery is preferred over generic site branding: obvious logos,
  avatars, placeholders, and explicitly tiny metadata previews are skipped.

## Channel identity

- Name: `Тренды и Бренды`.
- Avatar: supplied and managed by the channel owner outside this repository.
- Description:

  > 📈 Тренды и бренды
  >
  > Главные новости о компаниях, технологиях, бизнесе, людях и идеях, которые
  > меняют рынок и нашу жизнь.
  >
  > Новые продукты, громкие сделки, популярные бренды, свежие тренды и всё, о
  > чём будут говорить завтра.

- Regular posts use the original editorial image from the source. At 15:00 and
  19:00 Asia/Yekaterinburg the image becomes the background of a short branded
  MP4 card displayed directly in Telegram with the usual source caption.

The default settings consider the last three days, require a score of at least
eight, and select one story per run. The workflow is started through
`workflow_dispatch`; cron-job.org supplies the daily schedule. Manual runs
remain available. See [CRON_JOBS.md](CRON_JOBS.md) for the exact setup.

`AUTOPOSTER_MEDIA_MODE` controls media selection: `auto` uses the scheduled
slots, `photo` disables video for a run, and `video` forces it for a manual or
diagnostic run. A confirmed video stores its dated slot in publication history,
so restarting the same slot cannot publish a second clip. Rendering failure
falls back to the existing photo/text flow; uncertain Telegram delivery does
not fall back and therefore cannot create a duplicate.

When `PEXELS_API_KEY` is available, a video slot searches the official Pexels
API for neutral portrait B-roll mapped to the story category. The clip is
cropped, trimmed, and branded locally; its caption credits the creator and
links to the Pexels asset. Pexels footage is decorative context, never evidence
that the depicted people or brands participated in the reported event. Without
a key or suitable result, the existing animated editorial-image card is used.

To build a real channel, follow [PROJECT_SETUP.md](PROJECT_SETUP.md). For the
design and LiveCrime mapping, see [ARCHITECTURE.md](ARCHITECTURE.md).

## Safety

`AUTOPOSTER_DRY_RUN` defaults to `true`. A live Telegram send requires all of:

1. `AUTOPOSTER_DRY_RUN=false`;
2. valid `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID`;
3. an explicit execution of `main.py`.

Do not use real credentials in committed files. The workflow reads credentials
only from GitHub Secrets. Add `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` in
the repository's Settings → Secrets and variables → Actions before enabling
live scheduled publication.
