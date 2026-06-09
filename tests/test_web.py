def test_web_app_imports() -> None:
    from cbcb_software_crawler.web import app

    assert app.title == "CBCB Software Crawler"
