FROM python:3.12-slim
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir "poetry>=1.8,<2" \
    && poetry build \
    && ls -lah dist/
