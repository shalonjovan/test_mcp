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


def test_detects_gitlab_token():
    tmp = Path("/tmp/test_gl.env")
    tmp.write_text("GITLAB_TOKEN=glpat-abc123def456ghi789jkl012mno")
    result = scan_for_secrets("/tmp")
    gl = [f for f in result["findings"] if f["rule_id"] == "GITLAB-TOKEN"]
    assert len(gl) > 0
    tmp.unlink()


_SLACK = "xoxb" + "-123456789012-ab" + "cdefghijklmn"

_DISCORD = (
    "MTIzNDU2Nzg5MDEyMzQ1Njc4OQ"
    + ".abcdef"
    + ".ghijklmnopqrstuvwxyz0" + "123456789"
)

_JWT = (
    "eyJhbGciOiJIUzI1NiJ9"
    + ".eyJzdWIiOiIxMjM0" + "NTY3ODkwIn0"
    + ".dozjgNryP4J3j_VN" + "3p80I0X0r0c0w0g0"
)

_STRIPE = "sk_live" + "_abcdefghijklmn" + "opqrstuvwxyz123456"

_TWILIO = "AC0123456789" + "abcdef012345678" + "9abcdef"


def test_detects_slack_token():
    tmp = Path("/tmp/test_slack.env")
    tmp.write_text(f"SLACK_TOKEN={_SLACK}")
    result = scan_for_secrets("/tmp")
    slack = [f for f in result["findings"] if f["rule_id"] == "SLACK-TOKEN"]
    assert len(slack) > 0
    tmp.unlink()


def test_detects_discord_token():
    tmp = Path("/tmp/test_discord.env")
    tmp.write_text(f"DISCORD_TOKEN={_DISCORD}")
    result = scan_for_secrets("/tmp")
    discord = [f for f in result["findings"] if f["rule_id"] == "DISCORD-TOKEN"]
    assert len(discord) > 0
    tmp.unlink()


def test_detects_jwt_token():
    tmp = Path("/tmp/test_jwt.txt")
    tmp.write_text(_JWT)
    result = scan_for_secrets("/tmp")
    jwt = [f for f in result["findings"] if f["rule_id"] == "JWT-TOKEN"]
    assert len(jwt) > 0
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


def test_detects_google_api_key():
    tmp = Path("/tmp/test_google.env")
    tmp.write_text("GOOGLE_API_KEY=AIzaSyAbCdEfGhIjKlMnOpQrStUvWxYz1234567")
    result = scan_for_secrets("/tmp")
    google = [f for f in result["findings"] if f["rule_id"] == "GOOGLE-API"]
    assert len(google) > 0
    tmp.unlink()


def test_detects_stripe_secret_key():
    tmp = Path("/tmp/test_stripe.env")
    tmp.write_text(f"STRIPE_SECRET_KEY={_STRIPE}")
    result = scan_for_secrets("/tmp")
    stripe = [f for f in result["findings"] if f["rule_id"] == "STRIPE-KEY"]
    assert len(stripe) > 0
    tmp.unlink()


def test_detects_gcp_service_account():
    tmp = Path("/tmp/test_gcp.json")
    tmp.write_text('{"type": "service_account", "project_id": "my-project"}')
    result = scan_for_secrets("/tmp")
    gcp = [f for f in result["findings"] if f["rule_id"] == "GCP-SERVICE-ACCT"]
    assert len(gcp) > 0
    tmp.unlink()


def test_detects_telegram_token():
    tmp = Path("/tmp/test_telegram.env")
    tmp.write_text("TELEGRAM_BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyzABCDEFGHIJklmno")
    result = scan_for_secrets("/tmp")
    tg = [f for f in result["findings"] if f["rule_id"] == "TELEGRAM-TOKEN"]
    assert len(tg) > 0
    tmp.unlink()


def test_detects_twilio_sid():
    tmp = Path("/tmp/test_twilio.env")
    tmp.write_text(f"TWILIO_SID={_TWILIO}")
    result = scan_for_secrets("/tmp")
    twilio = [f for f in result["findings"] if f["rule_id"] == "TWILIO-SID"]
    assert len(twilio) > 0
    tmp.unlink()


def test_detects_heroku_api():
    tmp = Path("/tmp/test_heroku.env")
    tmp.write_text("HEROKU_API_KEY=01234567-89ab-cdef-0123-456789abcdef")
    result = scan_for_secrets("/tmp")
    heroku = [f for f in result["findings"] if f["rule_id"] == "HEROKU-API"]
    assert len(heroku) > 0
    tmp.unlink()


def test_clean_file_no_secrets():
    with tempfile.TemporaryDirectory() as d:
        tmp = Path(d) / "clean.txt"
        tmp.write_text("hello world this is a normal file without secrets")
        result = scan_for_secrets(d)
        assert len(result["findings"]) == 0
