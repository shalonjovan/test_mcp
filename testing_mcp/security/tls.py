from __future__ import annotations

import ssl
import socket
from typing import Any


def check_tls(hostname: str, port: int = 443, timeout: float = 10.0) -> dict[str, Any]:
    result: dict[str, Any] = {
        "hostname": hostname,
        "port": port,
        "certificate": {},
        "protocols": [],
        "passed": False,
    }

    try:
        context = ssl.create_default_context()
        with socket.create_connection((hostname, port), timeout=timeout) as sock:
            with context.wrap_socket(sock, server_hostname=hostname) as tls_sock:
                cert = tls_sock.getpeercert()
                version = tls_sock.version()

                result["protocols"].append(version)
                result["passed"] = True

                if cert:
                    subject = dict(cert.get("subject", [[("", "")]])[0])
                    issuer = dict(cert.get("issuer", [[("", "")]])[0])

                    result["certificate"] = {
                        "subject": subject.get("commonName", str(cert.get("subject", ""))),
                        "issuer": issuer.get("commonName", ""),
                        "version": cert.get("version", ""),
                        "serial_number": str(cert.get("serialNumber", "")),
                        "not_before": cert.get("notBefore", ""),
                        "not_after": cert.get("notAfter", ""),
                        "san": cert.get("subjectAltName", []),
                        "expired": _is_expired(cert.get("notAfter", "")),
                    }

    except ssl.SSLCertVerificationError as e:
        result["error"] = f"Certificate verification failed: {e}"
    except socket.timeout:
        result["error"] = "Connection timed out"
    except socket.gaierror:
        result["error"] = f"Could not resolve hostname: {hostname}"
    except ConnectionRefusedError:
        result["error"] = f"Connection refused to {hostname}:{port}"
    except Exception as e:
        result["error"] = str(e)

    return result


def _is_expired(not_after: str) -> dict[str, Any]:
    from datetime import datetime

    try:
        expiry = datetime.strptime(not_after, "%b %d %H:%M:%S %Y %Z")
        now = datetime.utcnow()
        remaining = (expiry - now).days
        return {
            "expired": remaining < 0,
            "days_remaining": remaining,
            "expiry_date": not_after,
        }
    except (ValueError, TypeError):
        return {"expired": False, "days_remaining": None, "expiry_date": not_after}
