"""Direct Russian-language sources for gadgets, AI, science, and technology."""

SOURCES = [
    {"name": "3DNews", "type": "rss", "url": "https://3dnews.ru/news/rss/", "enabled": True},
    {"name": "iXBT", "type": "rss", "url": "https://www.ixbt.com/export/news/rss.xml", "enabled": True},
    {"name": "Habr Новости", "type": "rss", "url": "https://habr.com/ru/rss/news/?fl=ru", "enabled": True},
    {"name": "N+1", "type": "rss", "url": "https://nplus1.ru/rss", "enabled": True},
    {"name": "Hi-Tech Mail", "type": "rss", "url": "https://hi-tech.mail.ru/rss/all/", "enabled": True},
    {"name": "SecurityLab", "type": "rss", "url": "https://www.securitylab.ru/_services/export/rss/", "enabled": True},
]

SOURCE_EXTRACTORS = {}
SOURCE_STOP_MARKERS = {
    "Habr Новости": ("читайте также", "реклама"),
    "Hi-Tech Mail": ("подпишитесь",),
}
