from app.bot.dsml_parser import parse_dsml_tool_calls, strip_dsml_blocks


def test_parse_patent_search_dsml():
    text = (
        '好的，正在搜索。<｜tool_calls> <｜invoke name="patent-search"> '
        '<｜parameter name="query" string="true">石墨烯</｜parameter> '
        '<｜parameter name="page" string="false">1</｜parameter> '
        '<｜parameter name="page_size" string="false">10</｜parameter> '
        "</｜invoke> </｜tool_calls>"
    )
    calls = parse_dsml_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "patent-search"
    assert calls[0]["arguments"]["query"] == "石墨烯"
    assert calls[0]["arguments"]["page"] == 1
    assert calls[0]["arguments"]["page_size"] == 10
    assert strip_dsml_blocks(text) == "好的，正在搜索。"


def test_parse_deepseek_function_calls_format():
    text = (
        "<｜DSML｜function_calls>"
        '<｜DSML｜invoke name="get_weather">'
        '<｜DSML｜parameter name="location" string="true">杭州</｜DSML｜parameter>'
        "</｜DSML｜invoke>"
        "</｜DSML｜function_calls>"
    )
    calls = parse_dsml_tool_calls(text)
    assert len(calls) == 1
    assert calls[0]["name"] == "get_weather"
    assert calls[0]["arguments"]["location"] == "杭州"
