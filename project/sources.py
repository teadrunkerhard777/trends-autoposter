"""Sources for the Trends & Brands channel."""


# Direct Russian industry feeds are combined with narrow Google News searches
# for international coverage. Google News entries retain the original article
# link and are filtered by the same project relevance rules as direct sources.
SOURCES = [
    {"name": "Postium Коллаборации", "type": "rss", "url": "https://postium.ru/tag/kollaby/feed/", "enabled": True},
    {"name": "AdIndex", "type": "rss", "url": "https://adindex.ru/news/news.rss", "enabled": True},
    {"name": "New Retail", "type": "rss", "url": "https://new-retail.ru/rss/index_all.php", "enabled": True},
    {"name": "Retail.ru", "type": "rss", "url": "https://www.retail.ru/rss/news/", "enabled": True},
    {
        "name": "Знаменитые бренды — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=%28Apple+OR+Samsung+OR+IKEA+OR+Nike+OR+adidas+OR+LEGO+OR+Netflix+OR+McDonald%27s+OR+Coca-Cola%29+%28collaboration+OR+launches+OR+unveils+OR+campaign+OR+limited+edition%29+when%3A3d&hl=en-US&gl=US&ceid=US%3Aen",
        "enabled": True,
    },
    {
        "name": "Бренды в России — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=%28Apple+OR+Samsung+OR+Wildberries+OR+Ozon+OR+Яндекс+OR+Сбер+OR+Т-Банк+OR+ВкусВилл+OR+Магнит+OR+Пятерочка%29+%28коллаборация+OR+выпустил+OR+представил+OR+запустил+OR+лимитка+OR+мем%29+when%3A3d&hl=ru&gl=RU&ceid=RU%3Aru",
        "enabled": True,
    },
    {
        "name": "Игры и развлечения — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=%28Netflix+OR+Disney+OR+Marvel+OR+Warner+Bros+OR+HBO+OR+PlayStation+OR+Xbox+OR+Nintendo+OR+Roblox+OR+GTA+OR+LEGO%29+%28collaboration+OR+launches+OR+campaign+OR+merch+OR+limited+edition%29+when%3A3d&hl=en-US&gl=US&ceid=US%3Aen",
        "enabled": True,
    },
    {
        "name": "Еда и мода — Google News", "type": "rss",
        "url": "https://news.google.com/rss/search?q=%28Nike+OR+adidas+OR+Crocs+OR+Gucci+OR+Dior+OR+Starbucks+OR+Coca-Cola+OR+Pepsi+OR+Lay%27s+OR+Oreo+OR+KitKat+OR+Nutella%29+%28collaboration+OR+new+flavor+OR+collection+OR+limited+edition%29+when%3A3d&hl=en-US&gl=US&ceid=US%3Aen",
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
