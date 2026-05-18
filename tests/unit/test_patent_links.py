from app.bot.patent_links import linkify_patent_ids


def test_linkify_plain_patent_id():
    text = "详见 CN113003031A 与 CN999999999A。"
    out = linkify_patent_ids(
        text,
        enabled=True,
        template="https://www.9235.net/patent/{patent_id}.html",
    )
    assert "[CN113003031A](https://www.9235.net/patent/CN113003031A.html)" in out
    assert "[CN999999999A](https://www.9235.net/patent/CN999999999A.html)" in out


def test_linkify_skips_existing_markdown():
    text = "已链接 [CN113003031A](https://example.com/p/1) 结束"
    out = linkify_patent_ids(text, enabled=True, template="https://www.9235.net/patent/{patent_id}.html")
    assert out.count("[CN113003031A]") == 1
