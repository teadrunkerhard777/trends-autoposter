from generation.pexels import PexelsVideo, search_pexels_video


class SearchResponse:
    def raise_for_status(self):
        return None

    def json(self):
        return {
            "videos": [{
                "url": "https://www.pexels.com/video/123/",
                "duration": 12,
                "user": {
                    "name": "Video Author",
                    "url": "https://www.pexels.com/@author",
                },
                "video_files": [
                    {
                        "file_type": "video/mp4",
                        "width": 1920,
                        "height": 1080,
                        "link": "https://video.test/landscape.mp4",
                    },
                    {
                        "file_type": "video/mp4",
                        "width": 1080,
                        "height": 1920,
                        "link": "https://video.test/portrait.mp4",
                    },
                ],
            }]
        }


def test_pexels_search_requests_portrait_and_selects_portrait_mp4(monkeypatch):
    request = {}

    def get(url, **kwargs):
        request.update(url=url, **kwargs)
        return SearchResponse()

    monkeypatch.setattr("generation.pexels.requests.get", get)
    result = search_pexels_video("creative studio", "secret-key", 8)

    assert result == PexelsVideo(
        file_url="https://video.test/portrait.mp4",
        page_url="https://www.pexels.com/video/123/",
        creator_name="Video Author",
        creator_url="https://www.pexels.com/@author",
        duration=12,
    )
    assert request["headers"] == {"Authorization": "secret-key"}
    assert request["params"]["orientation"] == "portrait"
    assert request["params"]["size"] == "medium"
