from testing_mcp.runners.mutation import MUTATIONS, _apply_mutation_ast


def test_mutation_types_defined():
    assert len(MUTATIONS) >= 5
    names = [m["name"] for m in MUTATIONS]
    assert "negate-condition" in names
    assert "swap-arithmetic" in names


def test_negate_condition():
    source = "if x > 5: pass"
    result = _apply_mutation_ast(source, "negate-condition")
    assert result is not None
    assert "<=" in result or "<" in result or ">" in result or ">=" in result


def test_swap_arithmetic():
    source = "y = a + b"
    result = _apply_mutation_ast(source, "swap-arithmetic")
    assert result is not None
    assert "-" in result


def test_replace_constant():
    source = "x = 0"
    result = _apply_mutation_ast(source, "replace-constant")
    assert result is not None
    assert "1" in result


def test_invalid_syntax():
    result = _apply_mutation_ast("this is not valid python {{{", "negate-condition")
    assert result is None
