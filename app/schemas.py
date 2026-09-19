"""Валидация данных из контактной формы портфолио."""

from __future__ import annotations

from pydantic import BaseModel, field_validator


class ContactForm(BaseModel):
    name: str
    contact: str
    message: str = ""
    # honeypot-поле: скрыто CSS от людей, но простые боты его заполняют.
    website: str = ""

    @field_validator("name")
    @classmethod
    def name_not_empty(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 2:
            raise ValueError("Имя должно быть не короче 2 символов")
        return value

    @field_validator("contact")
    @classmethod
    def contact_not_empty(cls, value: str) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError("Укажите email или телеграм для связи")
        return value

    def is_spam(self) -> bool:
        return bool(self.website.strip())
