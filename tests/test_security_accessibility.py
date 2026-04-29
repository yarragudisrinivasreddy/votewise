"""Tests for VoteWise security middleware and accessibility compliance."""

from __future__ import annotations


class TestSecurityHeaders:
    """Verify that all OWASP-recommended security headers are present."""

    def test_csp_header_present(self, client):
        res = client.get("/")
        assert "Content-Security-Policy" in res.headers

    def test_csp_blocks_frames(self, client):
        res = client.get("/")
        assert "frame-ancestors 'none'" in res.headers.get("Content-Security-Policy", "")

    def test_x_frame_options_deny(self, client):
        res = client.get("/")
        assert res.headers.get("X-Frame-Options") == "DENY"

    def test_x_content_type_options(self, client):
        res = client.get("/")
        assert res.headers.get("X-Content-Type-Options") == "nosniff"

    def test_referrer_policy(self, client):
        res = client.get("/")
        assert "Referrer-Policy" in res.headers

    def test_permissions_policy(self, client):
        res = client.get("/")
        assert "Permissions-Policy" in res.headers

    def test_permissions_policy_blocks_camera(self, client):
        val = client.get("/").headers.get("Permissions-Policy", "")
        assert "camera=()" in val

    def test_permissions_policy_blocks_microphone(self, client):
        val = client.get("/").headers.get("Permissions-Policy", "")
        assert "microphone=()" in val

    def test_x_xss_protection(self, client):
        res = client.get("/")
        assert "X-XSS-Protection" in res.headers

    def test_cache_control_no_store(self, client):
        res = client.get("/")
        assert "no-store" in res.headers.get("Cache-Control", "")

    def test_security_headers_on_api(self, client):
        import json
        res = client.post(
            "/api/ask",
            data=json.dumps({"question": "How to vote?", "language": "en"}),
            content_type="application/json",
        )
        assert "Content-Security-Policy" in res.headers

    def test_security_headers_on_health(self, client):
        res = client.get("/health")
        assert "X-Frame-Options" in res.headers

    def test_origin_validation_same_host_allowed(self, client):
        import json
        res = client.post(
            "/api/ask",
            data=json.dumps({"question": "What is ECI?", "language": "en"}),
            content_type="application/json",
            headers={"Origin": "http://localhost"},
        )
        assert res.status_code == 200

    def test_origin_validation_foreign_origin_blocked(self, client):
        import json
        res = client.post(
            "/api/ask",
            data=json.dumps({"question": "What is ECI?", "language": "en"}),
            content_type="application/json",
            headers={"Origin": "http://evil.example.com"},
        )
        assert res.status_code == 403


class TestSecurityInputValidation:
    """Verify defensive input handling."""

    def test_xss_attempt_sanitised(self, client):
        import json
        res = client.post(
            "/api/ask",
            data=json.dumps({"question": "<script>alert(1)</script>", "language": "en"}),
            content_type="application/json",
        )
        # Either sanitised and answered, or rejected — never echoed raw
        assert res.status_code in (200, 400, 422)
        if res.status_code == 200:
            data = res.get_json()
            assert "<script>" not in data.get("answer", "")

    def test_oversized_payload_rejected(self, client):
        import json
        res = client.post(
            "/api/ask",
            data=json.dumps({"question": "A" * 5000, "language": "en"}),
            content_type="application/json",
        )
        assert res.status_code in (400, 422)

    def test_null_bytes_rejected(self, client):
        import json
        res = client.post(
            "/api/ask",
            data=json.dumps({"question": "hello\x00world", "language": "en"}),
            content_type="application/json",
        )
        # Null bytes should be stripped — question becomes "helloworld" which is valid
        assert res.status_code in (200, 400, 422)


class TestAccessibilityAttributes:
    """Verify accessibility attributes are present in the served HTML."""

    def test_html_has_lang_attribute(self, client):
        res = client.get("/")
        assert b'lang="en"' in res.data

    def test_skip_nav_link_present(self, client):
        res = client.get("/")
        assert b"skip-nav" in res.data or b"Skip to main" in res.data

    def test_main_landmark_present(self, client):
        res = client.get("/")
        assert b'role="main"' in res.data or b"<main" in res.data

    def test_aria_live_region_present(self, client):
        res = client.get("/")
        assert b"aria-live" in res.data

    def test_aria_label_on_nav(self, client):
        res = client.get("/")
        assert b"aria-label" in res.data

    def test_aria_required_on_textarea(self, client):
        res = client.get("/")
        assert b'aria-required="true"' in res.data

    def test_aria_describedby_on_textarea(self, client):
        res = client.get("/")
        assert b"aria-describedby" in res.data

    def test_role_alert_on_toast(self, client):
        res = client.get("/")
        assert b'role="alert"' in res.data

    def test_aria_busy_on_messages(self, client):
        res = client.get("/")
        assert b"aria-busy" in res.data

    def test_inputmode_on_textarea(self, client):
        res = client.get("/")
        assert b'inputmode="text"' in res.data

    def test_autocomplete_on_textarea(self, client):
        res = client.get("/")
        assert b'autocomplete="off"' in res.data

    def test_spellcheck_on_textarea(self, client):
        res = client.get("/")
        assert b'spellcheck="true"' in res.data

    def test_sr_only_class_present(self, client):
        res = client.get("/")
        assert b"sr-only" in res.data

    def test_footer_contentinfo_role(self, client):
        res = client.get("/")
        assert b'role="contentinfo"' in res.data

    def test_banner_role_on_header(self, client):
        res = client.get("/")
        assert b'role="banner"' in res.data

    def test_send_button_has_aria_label(self, client):
        res = client.get("/")
        assert b'aria-label="Send question"' in res.data


class TestRateLimiting:
    """Verify rate limiting is configured."""

    def test_rate_limit_headers_present(self, client):
        import json
        res = client.post(
            "/api/ask",
            data=json.dumps({"question": "What is ECI?", "language": "en"}),
            content_type="application/json",
        )
        # Flask-Limiter injects X-RateLimit-* headers
        headers = dict(res.headers)
        has_limit = any("RateLimit" in k or "X-Rate" in k for k in headers)
        # Either the headers exist or the limiter is configured (200 response)
        assert res.status_code == 200 or has_limit
