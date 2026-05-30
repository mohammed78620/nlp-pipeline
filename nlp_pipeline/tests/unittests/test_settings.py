from nlp_pipeline.settings import VERSION


def test_settings():
    assert VERSION is not None
    assert type(VERSION) is str
    assert len(VERSION) > 0
