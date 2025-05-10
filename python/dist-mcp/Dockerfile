# ---- Builder Stage ----

FROM python:3.10-slim-bookworm AS builder

WORKDIR /app

RUN pip install --no-cache-dir pdm

COPY LICENSE README.md pyproject.toml pdm.lock ./

COPY alation_ai_agent_mcp ./alation_ai_agent_mcp/
RUN pdm sync --no-editable --prod

# ---- Final Runtime Stage ----
FROM python:3.10-slim-bookworm

WORKDIR /app

# Create a non-root user and group for security best practices.
ARG APP_USER_UID=10001
RUN useradd --uid ${APP_USER_UID} --user-group --system --create-home --home-dir /app --shell /sbin/nologin appuser

# Copy the virtual environment (which includes all installed dependencies).
COPY --from=builder --chown=appuser:appuser /app/.venv ./.venv

COPY --from=builder --chown=appuser:appuser /app/alation_ai_agent_mcp ./alation_ai_agent_mcp/

# Add the virtual environment's bin directory to the PATH.
ENV PATH="/app/.venv/bin:$PATH"
ENV VIRTUAL_ENV="/app/.venv"
ENV PYTHONPATH="/app:${PYTHONPATH}"
# Prevent Python from writing .pyc files.
ENV PYTHONDONTWRITEBYTECODE=1
# Ensure Python output is unbuffered (standard for container logs).
ENV PYTHONUNBUFFERED=1

USER appuser

ENTRYPOINT ["python", "-m", "alation_ai_agent_mcp.server"]