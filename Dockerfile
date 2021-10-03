FROM registry.gitlab.com/polytechnique-montr-al/inf3995/20213/equipe-100/inf3995-backend/ci:0.0.2 as builder

WORKDIR /build-directory

COPY pyproject.toml poetry.lock ./
COPY /backend ./backend

RUN poetry config virtualenvs.in-project true && \
    poetry install --no-dev && \
    poetry build

FROM python:3.9-slim-bullseye

WORKDIR /backend

# Install dependencies
RUN apt-get update && apt-get install libusb-1.0-0 -y

# Install the package
COPY --from=builder /build-directory/dist/*.tar.gz backend.tar.gz
RUN pip install ./backend.tar.gz

EXPOSE 8000
ENTRYPOINT ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
