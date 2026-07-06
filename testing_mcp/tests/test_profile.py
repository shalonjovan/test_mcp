from testing_mcp.performance.profiler import (
    get_cpu_info,
    get_disk_io,
    get_network_io,
    measure_memory_usage,
)


def test_measure_memory():
    result = measure_memory_usage()
    assert "rss_mb" in result or "rss_kb" in result


def test_get_cpu_info():
    result = get_cpu_info()
    assert isinstance(result, dict)
    if "cpu0" in result or "cpu" in result:
        assert "usage_percent" in list(result.values())[0]


def test_get_network_io():
    result = get_network_io()
    assert isinstance(result, dict)


def test_get_disk_io():
    result = get_disk_io()
    assert isinstance(result, dict)
