"""Отправка email-уведомления владельцу о новой заявке.

Через обычный smtplib — без сторонних сервисов вроде SendGrid, чтобы
не тащить лишнюю зависимость ради демо-проекта. В README отдельно
объяснено, как включить и на что заменить в проде (например, если
трафик вырастет — на транзакционный email-сервис с трекингом доставки).
"""

from __future__ import annotations

import logging
import os
import smtplib
from email.message import EmailMessage

from app.models import Lead

logger = logging.getLogger(__name__)


def notifications_enabled() -> bool:
    return os.getenv("EMAIL_NOTIFICATIONS_ENABLED", "false").lower() == "true"


def send_new_lead_notification(lead: Lead) -> None:
    if not notifications_enabled():
        return

    smtp_host = os.getenv("SMTP_HOST", "")
    smtp_port = int(os.getenv("SMTP_PORT", "587"))
    smtp_user = os.getenv("SMTP_USER", "")
    smtp_password = os.getenv("SMTP_PASSWORD", "")
    notify_to = os.getenv("NOTIFY_TO_EMAIL", "")

    if not all([smtp_host, smtp_user, smtp_password, notify_to]):
        logger.warning(
            "EMAIL_NOTIFICATIONS_ENABLED=true, но SMTP-настройки заполнены не "
            "полностью — уведомление не отправлено"
        )
        return

    message = EmailMessage()
    message["Subject"] = f"Новое сообщение с портфолио: {lead.name}"
    message["From"] = smtp_user
    message["To"] = notify_to
    message.set_content(
        f"Имя: {lead.name}\n"
        f"Контакт: {lead.contact}\n\n"
        f"Сообщение:\n{lead.message}"
    )

    try:
        with smtplib.SMTP(smtp_host, smtp_port, timeout=10) as smtp:
            smtp.starttls()
            smtp.login(smtp_user, smtp_password)
            smtp.send_message(message)
    except Exception:
        # Отправка уведомления не должна ронять сохранение заявки — заявка
        # уже в БД, письмо это просто удобство. Логируем и идём дальше.
        logger.exception("не удалось отправить email-уведомление о заявке %s", lead.id)
