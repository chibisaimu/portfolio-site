"""Тесты валидации контактной формы и rate limiter.

Не трогают FastAPI/БД напрямую — только схему валидации и rate limiter,
это чистая логика, которую можно проверить без поднятия сервера.
"""

import time

from app.rate_limit import RateLimiter
from app.schemas import ContactForm


def test_contact_form_valid():
    form = ContactForm(name="Алина", contact="alina@example.com", message="Привет")
    assert form.is_spam() is False


def test_contact_form_rejects_short_name():
    try:
        ContactForm(name="А", contact="alina@example.com")
        assert False, "должно было выбросить ValidationError"
    except Exception as exc:
        assert "Имя" in str(exc)


def test_contact_form_rejects_short_contact():
    try:
        ContactForm(name="Алина", contact="ab")
        assert False, "должно было выбросить ValidationError"
    except Exception as exc:
        assert "связи" in str(exc)


def test_contact_form_honeypot_marks_spam():
    form = ContactForm(name="Бот", contact="bot@example.com", website="http://spam.example")
    assert form.is_spam() is True


def test_rate_limiter_blocks_after_limit():
    limiter = RateLimiter(max_requests=2, window_seconds=60)
    assert limiter.allow("1.1.1.1") is True
    assert limiter.allow("1.1.1.1") is True
    assert limiter.allow("1.1.1.1") is False


def test_rate_limiter_resets_after_window():
    limiter = RateLimiter(max_requests=1, window_seconds=1)
    assert limiter.allow("2.2.2.2") is True
    assert limiter.allow("2.2.2.2") is False
    time.sleep(1.1)
    assert limiter.allow("2.2.2.2") is True


def test_rate_limiter_tracks_ips_independently():
    limiter = RateLimiter(max_requests=1, window_seconds=60)
    assert limiter.allow("3.3.3.3") is True
    assert limiter.allow("4.4.4.4") is True
    assert limiter.allow("3.3.3.3") is False
