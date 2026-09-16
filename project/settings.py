"""Publication and deduplication settings for Trends & Brands."""

CHANNEL_TITLE = "Тренды и Бренды"
CHANNEL_DESCRIPTION = """📈 Тренды и бренды

Главные новости о компаниях, технологиях, бизнесе, людях и идеях, которые меняют рынок и нашу жизнь.

Новые продукты, громкие сделки, популярные бренды, свежие тренды и всё, о чём будут говорить завтра."""

NEWS_LOOKBACK_DAYS = 3
MAX_NEWS_PER_RUN = 1
MIN_PUBLICATION_SCORE = 8
POST_MODE = "single"

# A separate external cron runs native video posts between regular slots.
VIDEO_TIMEZONE = "Asia/Yekaterinburg"
VIDEO_PUBLICATION_HOURS = (13, 21)
VIDEO_DURATION_SECONDS = 8
VIDEO_CANVAS_SIZE = (1080, 1350)
PEXELS_VIDEO_ENABLED = True
VIDEO_STYLE = {
    "accent": "#FFD54A",
    "background": "#101319",
    "foreground": "#FFFFFF",
    "muted": "#D5D9E2",
}

EVENT_DEDUP_SETTINGS = {
    "text_limit": 1600, "time_window_hours": 48, "min_shared_tokens": 5,
    "min_token_overlap": 0.45, "min_token_jaccard": 0.20, "dense_match_tokens": 7,
    "stop_words": {"about", "after", "also", "from", "into", "more", "that", "their", "this", "with", "will", "your", "для", "или", "как", "что", "это", "при", "его", "она", "они", "после", "стал", "стала", "бренд", "бренда", "компания", "компании"},
    "noise_prefixes": ("announce", "article", "company", "report", "source", "update", "анонс", "исследован", "компания", "новость", "отчет"),
}

DIVERSITY_SETTINGS = {
    "enabled": True, "text_limit": 1200, "core_min_shared_tokens": 4,
    "core_min_token_overlap": 0.30, "core_min_token_jaccard": 0.14,
    "core_dense_match_tokens": 5, "min_shared_tokens": 4,
    "min_token_overlap": 0.35, "min_token_jaccard": 0.16,
    "stop_words": EVENT_DEDUP_SETTINGS["stop_words"],
    "noise_prefixes": EVENT_DEDUP_SETTINGS["noise_prefixes"],
}
