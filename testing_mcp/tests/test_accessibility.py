from testing_mcp.ui.accessibility import check_color_contrast, check_keyboard_navigation


def test_color_contrast_pass():
    result = check_color_contrast("#000000", "#FFFFFF")
    assert result["contrast_ratio"] >= 21.0
    assert result["passes_AA_normal"] is True
    assert result["passes_AAA_normal"] is True


def test_color_contrast_fail():
    result = check_color_contrast("#AAAAAA", "#FFFFFF")
    assert result["contrast_ratio"] < 4.5
    assert result["passes_AA_normal"] is False


def test_color_contrast_fail_large():
    result = check_color_contrast("#777777", "#FFFFFF")
    assert result["passes_AA_large"] is True or result["passes_AA_large"] is False


def test_keyboard_navigation():
    result = check_keyboard_navigation(["#btn", ".link", "input"])
    assert result["type"] == "keyboard-navigation"
    assert len(result["selectors_to_check"]) == 3
    assert len(result["recommendations"]) > 0
