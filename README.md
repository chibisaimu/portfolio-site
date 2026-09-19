# Portfolio

Мой личный сайт-портфолио. Есть рабочая контактная форма (не просто mailto-ссылка): сообщения сохраняются в БД, опционально шлётся email-уведомление, есть honeypot и rate limiting от спама.

## Что внутри

- Одна страница: hero, обо мне, навыки, проекты (подтягиваются из списка в `main.py`), контакты
- Форма связи пишет в SQLite, с защитой от ботов (скрытое honeypot-поле) и лимитом 5 сообщений с одного IP за 10 минут
- Опциональная email-нотификация о новом сообщении через обычный SMTP

## Запуск

```bash
cp .env.example .env
docker compose up --build
```

Локально:
```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Тесты

```bash
pytest tests/
```

Проверяют валидацию формы и rate limiter — без поднятия сервера.

## Стек

FastAPI, Jinja2, SQLAlchemy, SQLite, Tailwind (через CDN), Docker
