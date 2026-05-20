from app.utils.outbound_assets import collect_outbound_assets, enrich_message_extra_data


def test_collect_outbound_assets_normalizes_links_images_and_files():
    assets = collect_outbound_assets(
        "请查看 [帮助中心](https://example.com/help) 和 [产品图](https://cdn.example.com/demo.png)",
        {
            "outbound_assets": [
                {
                    "type": "file",
                    "name": "产品手册",
                    "url": "https://example.com/manual.pdf",
                }
            ],
            "attachments": [
                {
                    "name": "现场照片.jpg",
                    "url": "https://cdn.example.com/photo.jpg",
                    "mime": "image/jpeg",
                }
            ],
        },
    )

    assert [asset["type"] for asset in assets] == ["file", "image", "link", "image"]
    assert assets[0]["name"] == "产品手册"
    assert assets[1]["source"] == "attachment"
    assert assets[2]["name"] == "帮助中心"
    assert assets[3]["url"] == "https://cdn.example.com/demo.png"


def test_enrich_message_extra_data_preserves_existing_fields_and_adds_assets():
    extra_data = enrich_message_extra_data(
        "参考 https://example.com/spec.docx",
        {"model": "gpt-5.4", "provider": "openai"},
    )

    assert extra_data is not None
    assert extra_data["model"] == "gpt-5.4"
    assert extra_data["provider"] == "openai"
    assert extra_data["outbound_assets"] == [
        {
            "type": "file",
            "name": "spec.docx",
            "url": "https://example.com/spec.docx",
            "source": "raw_url",
        }
    ]