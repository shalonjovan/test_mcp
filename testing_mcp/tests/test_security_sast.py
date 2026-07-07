from pathlib import Path

from testing_mcp.security.sast import SAST_RULES, run_sast_scan, scan_file


def test_sast_rules_are_defined():
    assert len(SAST_RULES) > 0
    for rule in SAST_RULES:
        assert "id" in rule
        assert "patterns" in rule
        assert len(rule["patterns"]) > 0
        assert "severity" in rule


def test_scan_file_detects_sqli_concat():
    tmp = Path("/tmp/test_sqli.py")
    tmp.write_text("import sqlite3\nconn = sqlite3.connect('test.db')\nconn.execute('SELECT * FROM users WHERE id = ' + user_input)")
    findings = scan_file(tmp)
    sqli = [f for f in findings if f["rule_id"] == "SQLI-001"]
    assert len(sqli) > 0
    tmp.unlink()


def test_scan_file_detects_sqli_fstring():
    tmp = Path("/tmp/test_sqli2.py")
    tmp.write_text('cursor.execute(f"SELECT * FROM users WHERE id = {uid}")')
    findings = scan_file(tmp)
    sqli = [f for f in findings if f["rule_id"] == "SQLI-002"]
    assert len(sqli) > 0
    tmp.unlink()


def test_scan_file_detects_xss_inner_html():
    tmp = Path("/tmp/test_xss.py")
    tmp.write_text("element.innerHTML = user_input")
    findings = scan_file(tmp)
    xss = [f for f in findings if f["rule_id"] == "XSS-001"]
    assert len(xss) > 0
    tmp.unlink()


def test_scan_file_detects_xss_template():
    tmp = Path("/tmp/test_xss2.py")
    tmp.write_text("{{ user_input|safe }}")
    findings = scan_file(tmp)
    xss = [f for f in findings if f["rule_id"] == "XSS-002"]
    assert len(xss) > 0
    tmp.unlink()


def test_scan_file_detects_hardcoded_password():
    tmp = Path("/tmp/test_secret.py")
    tmp.write_text('password = "super_secret_123"')
    findings = scan_file(tmp)
    secrets = [f for f in findings if f["rule_id"] == "SECRET-001"]
    assert len(secrets) > 0
    tmp.unlink()


def test_scan_file_detects_command_injection():
    tmp = Path("/tmp/test_cmdi.py")
    tmp.write_text('import os\nos.system(f"rm -rf {user_input}")')
    findings = scan_file(tmp)
    cmdi = [f for f in findings if f["rule_id"] == "CMDI-001"]
    assert len(cmdi) > 0
    tmp.unlink()


def test_scan_file_detects_nosql_injection():
    tmp = Path("/tmp/test_nosqli.js")
    tmp.write_text('db.users.find({ $where: "this.name == \'" + user + "\'" })')
    findings = scan_file(tmp)
    nosqli = [f for f in findings if f["rule_id"] == "NOSQLI-001"]
    assert len(nosqli) > 0
    tmp.unlink()


def test_scan_file_detects_csrf_exempt():
    tmp = Path("/tmp/test_csrf.py")
    tmp.write_text("@csrf_exempt\ndef login():\n    pass")
    findings = scan_file(tmp)
    csrf = [f for f in findings if f["rule_id"] == "CSRF-001"]
    assert len(csrf) > 0
    tmp.unlink()


def test_scan_file_detects_ssrf():
    tmp = Path("/tmp/test_ssrf.py")
    tmp.write_text('requests.get(f"https://{host}/api")')
    findings = scan_file(tmp)
    ssrf = [f for f in findings if f["rule_id"] == "SSRF-001"]
    assert len(ssrf) > 0
    tmp.unlink()


def test_scan_file_detects_path_traversal():
    tmp = Path("/tmp/test_pt.py")
    tmp.write_text('Path(f"/data/{user_file}").read_text()')
    findings = scan_file(tmp)
    pt = [f for f in findings if f["rule_id"] == "PT-001"]
    assert len(pt) > 0
    tmp.unlink()


def test_scan_file_detects_weak_crypto():
    tmp = Path("/tmp/test_crypto.py")
    tmp.write_text("import hashlib\nhashlib.md5(b'test')")
    findings = scan_file(tmp)
    crypto = [f for f in findings if f["rule_id"] == "CRYPTO-001"]
    assert len(crypto) > 0
    tmp.unlink()


def test_scan_file_detects_open_redirect():
    tmp = Path("/tmp/test_redirect.py")
    tmp.write_text('redirect(request.GET.get("next"))')
    findings = scan_file(tmp)
    redirect = [f for f in findings if f["rule_id"] == "OPEN-REDIRECT-001"]
    assert len(redirect) > 0
    tmp.unlink()


def test_scan_file_detects_xxe():
    tmp = Path("/tmp/test_xxe.py")
    tmp.write_text("from xml.etree import ElementTree\nElementTree.parse('file.xml')")
    findings = scan_file(tmp)
    xxe = [f for f in findings if f["rule_id"] == "XXE-001"]
    assert len(xxe) > 0
    tmp.unlink()


def test_scan_file_detects_deserialization():
    tmp = Path("/tmp/test_pickle.py")
    tmp.write_text("import pickle\npickle.loads(data)")
    findings = scan_file(tmp)
    deser = [f for f in findings if f["rule_id"] == "DESER-001"]
    assert len(deser) > 0
    tmp.unlink()


def test_scan_file_detects_ssti():
    tmp = Path("/tmp/test_ssti.py")
    tmp.write_text('from flask import render_template_string\nrender_template_string(f"Hello {name}")')
    findings = scan_file(tmp)
    ssti = [f for f in findings if f["rule_id"] == "SSTI-001"]
    assert len(ssti) > 0
    tmp.unlink()


def test_scan_file_detects_debug_mode():
    tmp = Path("/tmp/test_debug.py")
    tmp.write_text("DEBUG = True")
    findings = scan_file(tmp)
    debug = [f for f in findings if f["rule_id"] == "DEBUG-001"]
    assert len(debug) > 0
    tmp.unlink()


def test_scan_file_detects_cors_wildcard():
    tmp = Path("/tmp/test_cors.py")
    tmp.write_text('Access-Control-Allow-Origin: "*"')
    findings = scan_file(tmp)
    cors = [f for f in findings if f["rule_id"] == "CORS-001"]
    assert len(cors) > 0
    tmp.unlink()


def test_scan_file_detects_hardcoded_jwt():
    tmp = Path("/tmp/test_jwt.py")
    tmp.write_text('JWT_SECRET = "my_super_secret_key_12345"')
    findings = scan_file(tmp)
    jwt = [f for f in findings if f["rule_id"] == "HARDCODED-JWT-001"]
    assert len(jwt) > 0
    tmp.unlink()


def test_scan_file_detects_idor():
    tmp = Path("/tmp/test_idor.py")
    tmp.write_text("get_object_or_404(Model, pk=request.GET.get('id'))")
    findings = scan_file(tmp)
    idor = [f for f in findings if f["rule_id"] == "IDOR-001"]
    assert len(idor) > 0
    tmp.unlink()


def test_scan_file_detects_ldap_injection():
    tmp = Path("/tmp/test_ldap.py")
    tmp.write_text('conn.search("dc=example,dc=com", f"(uid={user})")')
    findings = scan_file(tmp)
    ldap = [f for f in findings if f["rule_id"] == "LDAPI-001"]
    assert len(ldap) > 0
    tmp.unlink()


def test_scan_file_detects_sensitive_file():
    tmp = Path("/tmp/test_envref.py")
    tmp.write_text("import os\nos.getenv('SECRET_KEY')")
    findings = scan_file(tmp)
    # Should NOT fire SENSITIVE-FILE-001 since it's looking for .env as file ref
    sf = [f for f in findings if f["rule_id"] == "SENSITIVE-FILE-001"]
    assert len(sf) == 0


def test_scan_file_detects_insecure_rng():
    tmp = Path("/tmp/test_rng.py")
    tmp.write_text("import random\nrandom.randint(0, 100)")
    findings = scan_file(tmp)
    rng = [f for f in findings if f["rule_id"] == "INSECURE-RNG-001"]
    assert len(rng) > 0
    tmp.unlink()


def test_scan_file_clean_code():
    tmp = Path("/tmp/test_clean.py")
    tmp.write_text("def hello():\n    return 'world'")
    findings = scan_file(tmp)
    assert len(findings) == 0
    tmp.unlink()


def test_run_sast_scan_returns_summary():
    result = run_sast_scan("/tmp")
    assert "tool" in result
    assert "findings" in result
    assert "summary" in result
    assert result["tool"] == "sast"
