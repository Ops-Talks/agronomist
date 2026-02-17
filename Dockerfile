FROM python:3.12-slim
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install poetry && poetry build && ls -lah dist/
