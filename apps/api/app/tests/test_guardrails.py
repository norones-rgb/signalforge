from app.services.safety import contains_blocked_content, contains_link, split_thread


def test_guardrails_blocklist():
    assert contains_blocked_content("You are subhuman") is True
    assert contains_blocked_content("Hello world") is False


def test_guardrails_link_detection():
    assert contains_link("Check https://example.com") is True
    assert contains_link("No links here") is False


def test_thread_splitter():
    text = "1) First tweet\n2) Second tweet"
    tweets = split_thread(text)
    assert tweets == ["First tweet", "Second tweet"]
