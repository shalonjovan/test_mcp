from __future__ import annotations

import json

import pytest

from testing_mcp.performance.load_test import run_load_test


def test_load_test_invalid_url():
    result = run_load_test("http://invalid.example.test:1", duration=2, concurrent_users=2)
    assert result["url"] == "http://invalid.example.test:1"
    assert isinstance(result["total_requests"], int)
    assert result["failed"] >= 0
    assert result["successful"] >= 0
    assert result["total_requests"] == result["successful"] + result["failed"]
    assert "latency_ms" in result
    assert "status_codes" in result
    assert "requests_per_sec" in result
    assert "error_rate" in result


def test_load_test_result_structure():
    result = run_load_test("http://invalid.example.test:1", duration=2, concurrent_users=1)
    required_keys = {
        "url", "method", "concurrent_users", "planned_duration", "ramp_up",
        "actual_duration", "total_requests", "successful", "failed",
        "error_rate", "requests_per_sec", "throughput_mbps",
        "total_bytes", "latency_ms", "status_codes", "errors",
    }
    assert required_keys.issubset(result.keys())
    assert result["method"] == "GET"
    assert "min" in result["latency_ms"]
    assert "p50" in result["latency_ms"]
    assert "p95" in result["latency_ms"]
    assert "p99" in result["latency_ms"]


def test_load_test_post_method():
    result = run_load_test(
        "http://invalid.example.test:1",
        method="POST",
        body='{"key": "value"}',
        duration=2,
        concurrent_users=2,
    )
    assert result["method"] == "POST"


def test_load_test_think_time():
    result = run_load_test(
        "http://invalid.example.test:1",
        duration=2,
        concurrent_users=2,
        think_time=0.1,
    )
    assert result["think_time"] == 0.1
    assert result["actual_duration"] >= 1.5


def test_load_test_ramp_up():
    result = run_load_test(
        "http://invalid.example.test:1",
        duration=3,
        concurrent_users=5,
        ramp_up=3,
    )
    assert result["ramp_up"] == 3
    assert result["concurrent_users"] == 5


def test_load_test_headers():
    headers = json.dumps({"Authorization": "Bearer test123", "X-Custom": "value"})
    result = run_load_test(
        "http://invalid.example.test:1",
        headers=headers,
        duration=1,
        concurrent_users=1,
    )
    assert result["errors"] is not None


def test_load_test_zero_duration():
    result = run_load_test("http://invalid.example.test:1", duration=0, concurrent_users=1)
    assert result["total_requests"] == 0
    assert result["actual_duration"] < 1


def test_load_test_error_rate():
    result = run_load_test("http://invalid.example.test:1", duration=2, concurrent_users=3)
    total = result["total_requests"]
    if total > 0:
        expected_error_rate = round(result["failed"] / total * 100, 2)
        assert result["error_rate"] == expected_error_rate
