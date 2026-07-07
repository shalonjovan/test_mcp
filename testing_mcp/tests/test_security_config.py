from pathlib import Path

from testing_mcp.security.config_scanner import (
    DOCKER_CHECKS,
    K8S_CHECKS,
    CI_CHECKS,
    scan_file,
    scan_directory,
)


def test_docker_checks_defined():
    assert len(DOCKER_CHECKS) >= 8
    ids = {c["id"] for c in DOCKER_CHECKS}
    assert "DOCKER-001" in ids


def test_k8s_checks_defined():
    assert len(K8S_CHECKS) >= 8
    ids = {c["id"] for c in K8S_CHECKS}
    assert "K8S-001" in ids


def test_ci_checks_defined():
    assert len(CI_CHECKS) >= 4


def test_scan_dockerfile_no_user():
    path = Path("/tmp/test_Dockerfile")
    path.write_text("FROM python:3.11\nRUN pip install flask\nCOPY . /app\nCMD python app.py\n")
    findings = scan_file(path, DOCKER_CHECKS)
    ids = {f["rule_id"] for f in findings}
    assert "DOCKER-001" in ids
    assert "DOCKER-010" in ids
    path.unlink()


def test_scan_dockerfile_with_user():
    path = Path("/tmp/test_Dockerfile2")
    path.write_text("FROM python:3.11\nRUN pip install flask\nUSER 1000\nCOPY . /app\nCMD python app.py\nHEALTHCHECK NONE\n")
    findings = scan_file(path, DOCKER_CHECKS)
    ids = {f["rule_id"] for f in findings}
    assert "DOCKER-001" not in ids
    path.unlink()


def test_scan_dockerfile_add_instead_of_copy():
    path = Path("/tmp/test_Dockerfile3")
    path.write_text("FROM ubuntu:22.04\nADD . /app\n")
    findings = scan_file(path, DOCKER_CHECKS)
    add = [f for f in findings if f["rule_id"] == "DOCKER-004"]
    assert len(add) > 0
    path.unlink()


def test_scan_dockerfile_latest_tag():
    path = Path("/tmp/test_Dockerfile4")
    path.write_text("FROM ubuntu:latest\n")
    findings = scan_file(path, DOCKER_CHECKS)
    latest = [f for f in findings if f["rule_id"] == "DOCKER-009"]
    assert len(latest) > 0
    path.unlink()


def test_scan_k8s_privileged():
    path = Path("/tmp/test_k8s.yaml")
    path.write_text("apiVersion: v1\nkind: Pod\nspec:\n  containers:\n  - name: test\n    securityContext:\n      privileged: true\n")
    findings = scan_file(path, K8S_CHECKS)
    priv = [f for f in findings if f["rule_id"] == "K8S-001"]
    assert len(priv) > 0
    path.unlink()


def test_scan_k8s_host_network():
    path = Path("/tmp/test_k8s2.yaml")
    path.write_text("apiVersion: v1\nkind: Pod\nspec:\n  hostNetwork: true\n  containers:\n  - name: test\n    image: nginx\n")
    findings = scan_file(path, K8S_CHECKS)
    hn = [f for f in findings if f["rule_id"] == "K8S-003"]
    assert len(hn) > 0
    path.unlink()


def test_scan_ci_hardcoded_secret():
    path = Path("/tmp/test_ci.yaml")
    path.write_text("jobs:\n  build:\n    steps:\n    - run: echo password='hunter2'\n")
    findings = scan_file(path, CI_CHECKS)
    secret = [f for f in findings if f["rule_id"] == "CI-001"]
    assert len(secret) > 0
    path.unlink()


def test_scan_directory_finds_dockerfile():
    findings = scan_directory("/tmp")
    assert "tool" in findings
