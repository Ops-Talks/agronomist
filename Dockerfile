# Pin to a digest in CI: --build-arg PYTHON_IMAGE=python:3.12-slim@sha256:<hash>
ARG PYTHON_IMAGE=python:3.12-slim
FROM ${PYTHON_IMAGE}
WORKDIR /build
COPY pyproject.toml README.md ./
COPY src ./src
RUN pip install --no-cache-dir "poetry>=1.8,<2" \
    && poetry build \
    && ls -lah dist/
