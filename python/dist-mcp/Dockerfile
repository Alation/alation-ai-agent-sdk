# Alation MCP Server Dockerfile
#
# This multi-stage Dockerfile uses distroless images for enhanced security and smaller image size.
# Builder stage uses Python 3.11 slim, runtime uses Google's distroless Python 3.11 image.
# The final image contains only the Python runtime and application dependencies.
#
# This container supports both STDIO and HTTP transport modes:
#
# STDIO Mode (default) - requires auth env vars:
#   docker run --env-file .env alation-mcp-server
#   # OR with explicit env vars:
#   docker run -e ALATION_BASE_URL=https://your-instance.alationcloud.com \
#              -e ALATION_AUTH_METHOD=user_account \
#              -e ALATION_USER_ID=123 \
#              -e ALATION_REFRESH_TOKEN=your_token \
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
#   ALATION_AUTH_METHOD=user_account|service_account
#   For user_account: ALATION_USER_ID, ALATION_REFRESH_TOKEN
#   For service_account: ALATION_CLIENT_ID, ALATION_CLIENT_SECRET
#
# Environment Variables for HTTP Mode:
#   Authentication is handled via OAuth in the web interface - no credentials needed in env vars
#
# Optional Environment Variables:
#   ALATION_DISABLED_TOOLS=tool1,tool2
#   ALATION_ENABLED_BETA_TOOLS=beta_tool1,beta_tool2
#   MCP_EXTERNAL_URL=https://external-host:8000 (for OAuth in HTTP mode)
# ---- Builder Stage ----

FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY LICENSE README.md pyproject.toml pdm.lock ./

COPY alation_ai_agent_mcp ./alation_ai_agent_mcp/
RUN pdm sync --no-editable --prod

# ---- Final Runtime Stage ----
FROM python:3.10-slim-bookworm

# Metadata labels for image information
LABEL org.opencontainers.image.title="Alation MCP Server" \
    org.opencontainers.image.description="Alation AI Agent SDK with Model Context Protocol (MCP) support for both STDIO and HTTP transport modes" \
    org.opencontainers.image.version="0.10.3" \
    org.opencontainers.image.vendor="Alation" \
    org.opencontainers.image.authors="Alation Team<ai_agent_sdk@alation.com>" \
    org.opencontainers.image.maintainer="Alation Team<ai_agent_sdk@alation.com>" \
    org.opencontainers.image.url="https://github.com/Alation/alation-ai-agent-sdk" \
    org.opencontainers.image.source="https://github.com/Alation/alation-ai-agent-sdk" \
    org.opencontainers.image.documentation="https://github.com/Alation/alation-ai-agent-sdk/tree/main/python/dist-mcp" \
    org.opencontainers.image.licenses="Apache-2.0" \
    org.opencontainers.image.base.name="python:3.10-slim-bookworm" \
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
ENV PYTHONPATH="/app:${PYTHONPATH}"
# Prevent Python from writing .pyc files
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure Python output is unbuffered
ENV PYTHONUNBUFFERED=1

USER appuser
EXPOSE 8000

ENTRYPOINT ["python", "-m", "alation_ai_agent_mcp"]