from __future__ import annotations

import ast
import subprocess
import tempfile
import time
from pathlib import Path
from typing import Any

MUTATIONS: list[dict[str, Any]] = [
    {"name": "negate-condition", "description": "Negate boolean condition (> to <=, == to !=)"},
    {"name": "remove-call", "description": "Remove a function/method call"},
    {"name": "swap-arithmetic", "description": "Swap arithmetic operators (+ to -, * to /)"},
    {"name": "replace-constant", "description": "Replace numeric constant (0 to 1, 1 to -1)"},
    {"name": "remove-return", "description": "Remove return statement"},
    {"name": "swap-boolean", "description": "Swap boolean (True to False, and to or)"},
]


def _apply_mutation_ast(source: str, mutation_type: str) -> str | None:
    class Mutator(ast.NodeTransformer):
        def visit_Compare(self, node):
            if mutation_type == "negate-condition":
                if isinstance(node.ops[0], ast.Gt):
                    node.ops[0] = ast.LtE()
                elif isinstance(node.ops[0], ast.Lt):
                    node.ops[0] = ast.GtE()
                elif isinstance(node.ops[0], ast.GtE):
                    node.ops[0] = ast.Lt()
                elif isinstance(node.ops[0], ast.LtE):
                    node.ops[0] = ast.Gt()
                elif isinstance(node.ops[0], ast.Eq):
                    node.ops[0] = ast.NotEq()
                elif isinstance(node.ops[0], ast.NotEq):
                    node.ops[0] = ast.Eq()
            return node

        def visit_BinOp(self, node):
            if mutation_type == "swap-arithmetic":
                if isinstance(node.op, ast.Add):
                    node.op = ast.Sub()
                elif isinstance(node.op, ast.Sub):
                    node.op = ast.Add()
                elif isinstance(node.op, ast.Mult):
                    node.op = ast.FloorDiv()
                elif isinstance(node.op, ast.FloorDiv):
                    node.op = ast.Mult()
            return node

        def visit_Constant(self, node):
            if mutation_type == "replace-constant" and isinstance(node.value, (int, float)):
                if node.value == 0:
                    node.value = 1
                elif node.value == 1:
                    node.value = 0
                elif node.value == -1:
                    node.value = 1
                else:
                    node.value = node.value + 1
            return node

        def visit_Return(self, node):
            if mutation_type == "remove-return":
                return None
            return node

        def visit_BoolOp(self, node):
            if mutation_type == "swap-boolean":
                if isinstance(node.op, ast.And):
                    node.op = ast.Or()
                elif isinstance(node.op, ast.Or):
                    node.op = ast.And()
            return node

        def visit_NameConstant(self, node):
            if mutation_type == "swap-boolean":
                if node.value is True:
                    return ast.Constant(value=False)
                elif node.value is False:
                    return ast.Constant(value=True)
            return node

    try:
        tree = ast.parse(source)
        tree = Mutator().visit(tree)
        ast.fix_missing_locations(tree)
        return ast.unparse(tree)
    except SyntaxError:
        return None


def run_mutation_test(
    source_file: str,
    test_command: str,
    mutation_types: list[str] | None = None,
    timeout: int = 60,
) -> dict[str, Any]:
    src = Path(source_file)
    if not src.exists():
        return {"error": f"File not found: {source_file}"}

    types = mutation_types or [m["name"] for m in MUTATIONS]
    source = src.read_text()

    results: list[dict[str, Any]] = []

    for mutation_type in types:
        mutated = _apply_mutation_ast(source, mutation_type)
        if mutated is None or mutated == source:
            continue

        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(mutated)
            tmp_path = f.name

        start = time.time()
        try:
            actual_cmd = test_command.replace("{file}", tmp_path)
            proc = subprocess.run(
                actual_cmd.split(),
                capture_output=True,
                text=True,
                timeout=timeout,
            )
            killed = proc.returncode == 0
        except subprocess.TimeoutExpired:
            killed = False
        except Exception as e:
            killed = False

        Path(tmp_path).unlink(missing_ok=True)
        duration = round(time.time() - start, 3)

        results.append({
            "mutation": mutation_type,
            "killed": killed,
            "duration": duration,
            "survived": not killed,
        })

    killed = sum(1 for r in results if r["killed"])
    total = len(results)
    score = round((killed / total) * 100, 1) if total > 0 else 0

    return {
        "source_file": source_file,
        "mutations_applied": total,
        "killed": killed,
        "survived": total - killed,
        "mutation_score": score,
        "results": results,
    }
