FROM python:3.9-slim-bullseye

# Install curl
RUN apt-get update && apt-get install curl -y

# Install Poetry
ENV POETRY_HOME="/opt/poetry"
ENV PATH="$POETRY_HOME/bin:$PATH"
RUN curl -sSL https://raw.githubusercontent.com/python-poetry/poetry/master/install-poetry.py | python -

WORKDIR /app

COPY pyproject.toml poetry.lock ./
COPY backend ./backend

RUN poetry config virtualenvs.create false
RUN poetry install --no-dev

EXPOSE 8000
ENTRYPOINT ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
