# ==========================================
# Builder Stage: Install dependencies
# ==========================================
FROM python:3.14-slim AS builder

# Set standard Python environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Create a virtual environment
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Install dependencies into the venv
COPY requirements.txt .
# Upgrading pip is generally a good practice, followed by your installs
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ==========================================
# Final Stage: Run the application
# ==========================================
FROM python:3.14-slim

# Copy environment variables, including the venv path
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    PATH="/opt/venv/bin:$PATH"

WORKDIR /app

# Create a non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser /app

# Copy only the compiled dependencies from the builder stage
COPY --from=builder /opt/venv /opt/venv

# Copy application code with proper ownership
COPY --chown=appuser:appuser . .

# Switch to the non-root user
USER appuser

EXPOSE 29920

CMD ["python", "main.py"]