FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /srv/backend

RUN addgroup --system app && adduser --system --ingroup app app
COPY backend/requirements.txt ./requirements-backend.txt
COPY RAG/requirements.txt /srv/RAG/requirements.txt
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements-backend.txt

COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/scripts ./scripts
COPY backend/src ./src
COPY RAG/app /srv/RAG/app

RUN chown -R app:app /srv
USER app

EXPOSE 8000
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
