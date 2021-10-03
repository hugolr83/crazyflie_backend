FROM python:3.9-slim-bullseye

ARG BACKEND_VERSION
ARG PYPI_REPO_URL

# Install dependencies
RUN apt-get update && apt-get install libusb-1.0-0 -y

# Install the package
RUN pip install backend==$BACKEND_VERSION --index-url $PYPI_REPO_URL --no-cache-dir

EXPOSE 8000
ENTRYPOINT ["uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
