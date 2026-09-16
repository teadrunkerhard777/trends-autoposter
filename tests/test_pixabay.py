from generation.pixabay import PixabayVideo, search_pixabay_video


class SearchResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "hits": [{
                "pageURL": "https://pixabay.com/videos/id-456/",
                "duration": 15,
                "user": "Video Author",
                "user_id": 42,
                "videos": {
                    "medium": {
                        "url": "https://cdn.test/landscape.mp4",
                        "width": 1920,
                        "height": 1080,
                        "size": 1000,
                    },
                    "small": {
                        "url": "https://cdn.test/portrait.mp4",
                        "width": 1080,
                        "height": 1920,
                        "size": 900,
                    },
                },
            }]
        }


def test_pixabay_search_is_safe_vertical_and_cached(monkeypatch, tmp_path):
    requests = []

    def get(url, **kwargs):
        requests.append((url, kwargs))
        return SearchResponse()

    monkeypatch.setattr("generation.pixabay.requests.get", get)
    cache_path = tmp_path / "searches.json"
    first = search_pixabay_video("creative studio", "api-key", 8, cache_path)
    second = search_pixabay_video("creative studio", "api-key", 8, cache_path)

    assert first == second == PixabayVideo(
        file_url="https://cdn.test/portrait.mp4",
        page_url="https://pixabay.com/videos/id-456/",
        creator_name="Video Author",
        creator_url="https://pixabay.com/users/Video-Author-42/",
        duration=15,
    )
    assert len(requests) == 1
    assert requests[0][1]["params"]["safesearch"] == "true"
    assert requests[0][1]["params"]["video_type"] == "film"
