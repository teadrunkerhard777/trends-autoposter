"""Sources for the Trends & Brands channel."""


# Direct Russian industry feeds are combined with narrow Google News searches
# for international coverage. Google News entries retain the original article
# link and are filtered by the same project relevance rules as direct sources.
SOURCES = [
    {"name": "Cossa", "type": "rss", "url": "https://www.cossa.ru/rss/", "enabled": True},
    {"name": "AdIndex", "type": "rss", "url": "https://adindex.ru/news/news.rss", "enabled": True},
    {"name": "New Retail", "type": "rss", "url": "https://new-retail.ru/rss/index_all.php", "enabled": True},
    {"name": "Retail.ru", "type": "rss", "url": "https://www.retail.ru/rss/news/", "enabled": True},
    {
        "name": "Marketing Dive — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=site%3Amarketingdive.com+when%3A3d&hl=en-US&gl=US&ceid=US%3Aen",
        "enabled": True,
    },
    {
        "name": "Retail Dive — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=site%3Aretaildive.com+when%3A3d&hl=en-US&gl=US&ceid=US%3Aen",
        "enabled": True,
    },
    {
        "name": "The Drum — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=site%3Athedrum.com+when%3A3d&hl=en-US&gl=US&ceid=US%3Aen",
        "enabled": True,
    },
    {
        "name": "Design Week — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=site%3Adesignweek.co.uk+when%3A7d&hl=en-GB&gl=GB&ceid=GB%3Aen",
        "enabled": True,
    },
]

def extract_new_retail_article(soup):
    """Extract only the editorial body, excluding navigation and forms."""
    body = soup.select_one('[itemprop="articleBody"]')
    if body is None:
        return ""
    for node in body.select("script, style, noindex"):
        node.decompose()
    return "\n\n".join(body.stripped_strings)


def extract_retail_article(soup):
    """Extract the Retail.ru story without its subscription banner."""
    body = soup.select_one(".contain__description")
    if body is None:
        return ""
    for node in body.select("script, style"):
        node.decompose()
    return "\n\n".join(body.stripped_strings)


SOURCE_EXTRACTORS = {
    "New Retail": extract_new_retail_article,
    "Retail.ru": extract_retail_article,
}
SOURCE_STOP_MARKERS = {
    "New Retail": ("Согласен с политикой конфиденциальности",),
    "Retail.ru": ("Получайте новости индустрии ритейла первым",),
}
