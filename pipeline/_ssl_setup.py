"""TLS CA bundle setup for libraries that fail on non-ASCII home paths."""

from __future__ import annotations

import os
import shutil

import certifi

ASCII_CA = r"C:\temp\earnings_forecast\cacert.pem"


def ensure_ssl_env() -> None:
    """Set CA bundle environment variables before http/yfinance imports."""
    if not os.path.exists(ASCII_CA):
        os.makedirs(os.path.dirname(ASCII_CA), exist_ok=True)
        shutil.copy(certifi.where(), ASCII_CA)
    os.environ.setdefault("CURL_CA_BUNDLE", ASCII_CA)
    os.environ.setdefault("SSL_CERT_FILE", ASCII_CA)
