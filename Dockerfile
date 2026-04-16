FROM python:3.13-slim

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src
COPY docs ./docs
COPY simulators ./simulators

RUN pip install --no-cache-dir .

EXPOSE 8000

CMD ["uvicorn", "iot_monitoring.main:app", "--host", "0.0.0.0", "--port", "8000"]
