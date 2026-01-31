# Alation MCP Server Dockerfile
#
# This multi-stage Dockerfile uses slim images for enhanced security and smaller image size.
# Builder stage uses Python 3.10 slim for dependency installation via pip.
# Runtime stage uses Python 3.10 slim with only the virtual environment and application code.
#
# This container supports both STDIO and HTTP transport modes:
#
# STDIO Mode (default) - requires auth env vars:
#   docker run --env-file .env alation-mcp-server
#   # OR with explicit env vars:
#   docker run -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
#              -e ALATION_AUTH_METHOD=service_account \
#              -e ALATION_CLIENT_ID=your_client_id \
#              -e ALATION_CLIENT_SECRET=your_client_secret \
#              alation-mcp-server
#
# HTTP Mode - only base URL needed, auth via web OAuth:
#   docker run -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
#              -p 8000:8000 \
#              alation-mcp-server --transport http --host 0.0.0.0
#
# Environment Variables Required:
#   ALATION_BASE_URL=https://your-instance.alationcloud.com
#
# Environment Variables Required for STDIO Mode:
#   ALATION_AUTH_METHOD=service_account
#   For service_account: ALATION_CLIENT_ID, ALATION_CLIENT_SECRET
#
# Environment Variables for HTTP Mode:
#   Authentication is handled via OAuth in the web interface - no credentials needed in env vars
#
# Optional Environment Variables:
#   ALATION_DISABLED_TOOLS=tool1,tool2
#   ALATION_ENABLED_TOOLS=tool3,tool4,tool5,tool6
#   ALATION_ENABLED_BETA_TOOLS=beta_tool1,beta_tool2
#   MCP_EXTERNAL_URL=https://external-host:8000 (for OAuth in HTTP mode)
# ---- Builder Stage ----

FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

# Copy project files
COPY LICENSE README.md pyproject.toml ./
COPY alation_ai_agent_mcp ./alation_ai_agent_mcp/

# Create virtual environment and install dependencies from PyPI
# Note: uv.lock references local path dependencies, so we use pip for Docker builds
RUN python -m venv .venv && \
    .venv/bin/pip install --no-cache-dir --upgrade pip && \
    .venv/bin/pip install --no-cache-dir .

# ---- Final Runtime Stage ----
FROM python:3.10-slim-bookworm

# Version ARG - override at build time: docker build --build-arg VERSION=1.0.0 .
# Default "dev" is used for local builds; CI/CD should always pass explicit version
# The docker/metadata-action in GitHub workflow also sets version via labels
ARG VERSION=dev

# Metadata labels for image information
LABEL org.opencontainers.image.title="Alation MCP Server" \
    org.opencontainers.image.description="Alation AI Agent SDK with Model Context Protocol (MCP) support for both STDIO and HTTP transport modes" \
    org.opencontainers.image.version="${VERSION}" \
    org.opencontainers.image.vendor="Alation" \
    org.opencontainers.image.authors="Alation Team<ai_agent_sdk@alation.com>" \
    org.opencontainers.image.maintainer="Alation Team<ai_agent_sdk@alation.com>" \
    org.opencontainers.image.url="https://github.com/Alation/alation-ai-agent-sdk" \
    org.opencontainers.image.source="https://github.com/Alation/alation-ai-agent-sdk" \
    org.opencontainers.image.documentation="https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-mcp" \
    org.opencontainers.image.licenses="Apache-2.0" \
    maintainer="Alation AI Team <ai-team@alation.com>" \
    com.alation.component="mcp-server" \
    com.alation.transport.modes="stdio,http" \
    com.alation.python.version="3.10"

WORKDIR /app

ARG APP_USER_UID=10001
RUN useradd --uid ${APP_USER_UID} --user-group --system --create-home --home-dir /app --shell /sbin/nologin appuser

COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

COPY --from=builder --chown=appuser:appuser /app/alation_ai_agent_mcp ./alation_ai_agent_mcp/

ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV PYTHONPATH="/app"
# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

USER appuser
EXPOSE 8000

ENTRYPOINT ["start-alation-mcp-server"]
