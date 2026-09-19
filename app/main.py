"""FastAPI-приложение персонального портфолио: одна страница + приём сообщений."""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from dotenv import load_dotenv
from fastapi import Depends, FastAPI, Form, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db, init_db
from app.email_notify import send_new_lead_notification
from app.models import Lead
from app.rate_limit import RateLimiter
from app.schemas import ContactForm

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="Alina Kuchmenova — Portfolio")
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

contact_rate_limiter = RateLimiter(max_requests=5, window_seconds=600)

# Замени ссылки на реальные, когда запушишь соответствующие репозитории —
# названия ниже совпадают с теми, что уже обсуждались и собирались в этом
# портфолио, но GitHub-адрес нужно проверить самой перед деплоем.
PROJECTS = [
    {
        "name": "LLM RAG Assistant",
        "description": (
            "Ассистент вопрос-ответ по базе знаний на RAG: три стратегии "
            "промптинга (zero-shot/few-shot/CoT) со сравнением качества, "
            "ChromaDB, FastAPI + Streamlit."
        ),
        "stack": ["Python", "FastAPI", "ChromaDB", "Streamlit"],
        "url": "https://github.com/chibisaimu/llm-rag-assistant",
    },
    {
        "name": "Telegram Lead Bot",
        "description": (
            "Бот для сбора заявок на услуги через пошаговый FSM-диалог, "
            "с валидацией ввода и админ-командами для управления заявками."
        ),
        "stack": ["Python", "aiogram 3", "SQLAlchemy"],
        "url": "https://github.com/chibisaimu/telegram-lead-bot",
    },
    {
        "name": "Task API",
        "description": (
            "REST API на чистом Go с JWT-аутентификацией и CRUD задач. "
            "PostgreSQL напрямую через pgx, без ORM, слоистая архитектура."
        ),
        "stack": ["Go", "chi", "pgx", "PostgreSQL"],
        "url": "https://github.com/chibisaimu/task-api-go",
    },
    {
        "name": "Task Queue",
        "description": (
            "Сервис фоновой обработки задач с пулом воркеров-горутин и "
            "graceful shutdown. Тесты гоняются с -race — без гонок данных."
        ),
        "stack": ["Go", "goroutines", "channels"],
        "url": "https://github.com/chibisaimu/task-queue-go",
    },
]


def base_context(request: Request) -> dict:
    return {
        "projects": PROJECTS,
        "year": datetime.now(timezone.utc).year,
    }


@app.on_event("startup")
def on_startup() -> None:
    init_db()


@app.get("/", response_class=HTMLResponse)
def index(request: Request) -> HTMLResponse:
    context = base_context(request) | {"success": False, "errors": {}, "form": {}}
    return templates.TemplateResponse(request, "index.html", context)


@app.post("/contact", response_class=HTMLResponse)
def create_contact(
    request: Request,
    name: str = Form(...),
    contact: str = Form(...),
    message: str = Form(""),
    website: str = Form(""),  # honeypot
    db: Session = Depends(get_db),
) -> HTMLResponse:
    client_ip = request.client.host if request.client else "unknown"

    if not contact_rate_limiter.allow(client_ip):
        context = base_context(request) | {
            "success": False,
            "errors": {"__all__": "Слишком много сообщений подряд. Попробуйте позже."},
            "form": {"name": name, "contact": contact, "message": message},
        }
        return templates.TemplateResponse(request, "index.html", context, status_code=429)

    try:
        form = ContactForm(name=name, contact=contact, message=message, website=website)
    except ValidationError as exc:
        errors = {err["loc"][0]: err["msg"] for err in exc.errors()}
        context = base_context(request) | {
            "success": False,
            "errors": errors,
            "form": {"name": name, "contact": contact, "message": message},
        }
        return templates.TemplateResponse(request, "index.html", context, status_code=422)

    if form.is_spam():
        context = base_context(request) | {"success": True, "errors": {}, "form": {}}
        return templates.TemplateResponse(request, "index.html", context)

    lead = Lead(name=form.name, contact=form.contact, message=form.message)
    db.add(lead)
    db.commit()
    db.refresh(lead)

    send_new_lead_notification(lead)

    context = base_context(request) | {"success": True, "errors": {}, "form": {}}
    return templates.TemplateResponse(request, "index.html", context)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}

