"""Инициализация SQLAlchemy: engine, сессии, создание таблиц."""

from __future__ import annotations

import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


class Base(DeclarativeBase):
    pass


DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/leads.db")

# Для SQLite нужно убедиться, что каталог под файл БД существует —
# иначе создание engine/таблиц упадёт с "unable to open database file".
if DATABASE_URL.startswith("sqlite:///"):
    db_path = Path(DATABASE_URL.removeprefix("sqlite:///"))
    db_path.parent.mkdir(parents=True, exist_ok=True)

# check_same_thread=False нужен только для SQLite — по умолчанию он не
# позволяет использовать одно соединение из разных потоков, а uvicorn
# может обрабатывать запросы в пуле потоков.
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

engine = create_engine(DATABASE_URL, connect_args=connect_args)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db() -> None:
    Base.metadata.create_all(bind=engine)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
