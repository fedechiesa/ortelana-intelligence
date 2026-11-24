FROM python:3.12-slim@sha256:191083cdf6c7bda8c76158983163ead5d5cf7b77cf3033e805bb0f5296f51b4b AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY backend/requirements.lock /app/requirements.lock
RUN pip install --no-cache-dir --require-hashes -r requirements.lock
COPY backend /app
RUN useradd --create-home appuser && chown -R appuser:appuser /app
USER appuser
EXPOSE 8000
CMD ["sh", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 1 --timeout-keep-alive 10"]
