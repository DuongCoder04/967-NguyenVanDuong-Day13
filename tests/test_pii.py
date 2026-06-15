from app.pii import scrub_text


def test_scrub_email() -> None:
    out = scrub_text("Email me at student@vinuni.edu.vn")
    assert "student@" not in out
    assert "REDACTED_EMAIL" in out


def test_scrub_phone_vn() -> None:
    out = scrub_text("Call 0901234567 for support")
    assert "0901234567" not in out
    assert "REDACTED_PHONE_VN" in out


def test_scrub_phone_vn_codes() -> None:
    out = scrub_text("+84 901234567")
    assert "REDACTED_PHONE_VN" in out


def test_scrub_cccd() -> None:
    out = scrub_text("My ID is 079203000123")
    assert "079203000123" not in out
    assert "REDACTED_CCCD" in out


def test_scrub_credit_card() -> None:
    out = scrub_text("Card 4111-1111-1111-1111")
    assert "4111" not in out
    assert "REDACTED_CREDIT_CARD" in out


def test_scrub_passport_vn() -> None:
    out = scrub_text("Passport number C1234567")
    assert "C1234567" not in out
    assert "REDACTED_PASSPORT_VN" in out


def test_scrub_address_keywords() -> None:
    out = scrub_text("Located at Phường Bến Nghé")
    assert "REDACTED_ADDRESS_VN" in out
