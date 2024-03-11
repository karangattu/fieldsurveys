from fieldsurveys.app_files.utils import get_species_image


# TODO: Fix tests
def test_get_species_image_api_failure(monkeypatch):
    class MockResponse:
        def __init__(self, status_code):
            self.status_code = status_code

    def mock_get(*args, **kwargs):
        return MockResponse(500)

    monkeypatch.setattr("requests.get", mock_get)

    result = get_species_image("Genus", "Species", 0)

    # Assert that the result is the default image URL
    assert result == "https://i.ibb.co/m6YDp69/sorry.jpg"
