import tempfile
from pathlib import Path

from testing_mcp.security.secrets import SECRET_PATTERNS, scan_for_secrets


def test_secret_patterns_are_defined():
    assert len(SECRET_PATTERNS) > 0
    for rule in SECRET_PATTERNS:
        assert "id" in rule
        assert "pattern" in rule
        assert "severity" in rule


def test_detects_aws_key():
    tmp = Path("/tmp/test_aws.env")
    tmp.write_text("AWS_ACCESS_KEY_ID=AKIAIOSFODNN7EXAMPLE")
    result = scan_for_secrets("/tmp")
    aws = [f for f in result["findings"] if f["rule_id"] == "AWS-KEY"]
    assert len(aws) > 0
    tmp.unlink()


def test_detects_github_token():
    tmp = Path("/tmp/test_gh.env")
    tmp.write_text("GITHUB_TOKEN=ghp_abc123def456ghi789jkl012mno345pqr678st")
    result = scan_for_secrets("/tmp")
    gh = [f for f in result["findings"] if f["rule_id"] == "GITHUB-TOKEN"]
    assert len(gh) > 0
    tmp.unlink()


def test_detects_ssh_key():
    tmp = Path("/tmp/test_key.pem")
    tmp.write_text("-----BEGIN RSA PRIVATE KEY-----\nMIICXAIBAAKBgQ\n-----END RSA PRIVATE KEY-----")
    result = scan_for_secrets("/tmp")
    ssh = [f for f in result["findings"] if f["rule_id"] == "SSH-KEY"]
    assert len(ssh) > 0
    tmp.unlink()


def test_detects_db_connection_string():
    tmp = Path("/tmp/test_db.env")
    tmp.write_text('DATABASE_URL=postgresql://user:pass@localhost:5432/mydb')
    result = scan_for_secrets("/tmp")
    conn = [f for f in result["findings"] if f["rule_id"] == "CONNECTION-STRING"]
    assert len(conn) > 0
    tmp.unlink()


def test_clean_file_no_secrets():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "clean.txt"
        tmp.write_text("hello world this is a normal file without secrets")
        result = scan_for_secrets(d)
        assert len(result["findings"]) == 0
