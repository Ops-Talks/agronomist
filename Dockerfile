FROM python:3.12-slim

WORKDIR /app

# Install Poetry
RUN pip install --no-cache-dir poetry

# Copy project files
COPY pyproject.toml ./
COPY poetry.lock* ./
COPY src ./src
COPY README.md .

# Install dependencies
RUN poetry install --no-interaction --no-ansi

# Build package
RUN poetry build

# Ensure output directory exists
RUN mkdir -p /output && \
    cp -r dist/* /output/ && \
    ls -lah /output/

CMD ["sh", "-c", "echo 'Build artifacts:' && ls -lah /output/"]
