# «Ну и ГАДЖЕТЫ | Новости хай-тек» Autoposter

A rule-based Telegram autoposter for notable gadgets, electronics, artificial
intelligence, science, space, cybersecurity, and software news. Local
execution remains safe by default.

## What it includes

- RSS, declarative HTML, and local static collectors.
- A shared `news_item` data shape.
- Date filtering, project-owned relevance, scoring, and stable ranking.
- URL, title, and conservative cross-source event deduplication.
- Generic article text and `og:image` / `twitter:image` extraction.
- Isolated source-specific article extractors and stop markers.
- Telegram text/photo publishing with temporary-file fallback.
- Native eight-second MP4 cards for the separate 13:00 and 21:00 video slots.
- Licensed Pexels and Pixabay motion backgrounds with creator attribution.
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

The project uses direct Russian-language RSS feeds. Relevance, topic categories,
scoring, and Telegram presentation live in `project/`.

## Channel behavior

- Direct coverage: 3DNews, iXBT, Habr News, N+1, Hi-Tech Mail, and SecurityLab.
- Topics: gadgets, AI, science, space, cybersecurity, and major software news.
- Every accepted story needs a concrete launch, discovery, update, experiment,
  vulnerability, or other confirmed development.
- Discounts, roundups, reviews, guides, rumors, appointments, and weekly
  digests are excluded before scoring.
- Posts contain a headline, no more than two factual sentences, and a compact
  dated footer with the channel rubric, direct source link, and one hashtag.
- Article imagery is preferred over generic site branding: obvious logos,
  avatars, placeholders, and explicitly tiny metadata previews are skipped.

## Channel identity

- Name: `Ну и ГАДЖЕТЫ | Новости хай-тек`.
- Avatar: supplied and managed by the channel owner outside this repository.
- Description:

  > 📱 Ну и ГАДЖЕТЫ
  >
  > Гаджеты, электроника, ИИ, наука и технологии — коротко и по делу.
  >
  > Новые устройства, важные обновления, открытия и всё, что уже меняет нашу
  > жизнь.

- Regular posts use the original editorial image from the source. Separate
  video runs at 13:00 and 21:00 Asia/Yekaterinburg use Pexels or Pixabay
  motion, or turn the editorial image into a short branded MP4 card displayed
  directly in Telegram with the usual source caption.

The default settings consider the last three days, deeply inspect the top 25
candidates, and select one story per run. The workflow is started through
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

When `PIXABAY_API_KEY` is available, Pixabay is the second stock provider after
Pexels. Only safe portrait MP4 renditions are accepted, the contributor and
Pixabay asset are credited, and API search responses are cached for 24 hours.

Production uses two external cron tasks. `autoposter.yml` forces regular
photo/text posts and keeps the existing schedule. `video-autoposter.yml` forces
stock-backed video posts at 13:00 and 21:00 Asia/Yekaterinburg. Both workflows
share one concurrency group and one confirmed-publication history.

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
