FROM python:3.12-bullseye
ENV PYTHONUNBUFFERED=1

ADD . /venari
WORKDIR /venari

# Add uv CLI
COPY --from=ghcr.io/astral-sh/uv:0.7.8 /uv /uvx /bin/

# Install dependencies
RUN echo "Sync uv." && uv sync --locked

# Set PYTHONPATH so Python can import from ./src
ENV PYTHONPATH=/venari/src
