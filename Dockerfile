FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000

# Cairo is required by the supported local SVG rasterizer.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libcairo2 \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser

WORKDIR /app
# Copy the application allowlist only, never the repository or user exports.
COPY pyproject.toml README.md LICENSE server.py schemas.py generate_pptx.py ai_helper.py outline_markdown.py ./
COPY storyboard_studio/ ./storyboard_studio/
RUN pip install --no-cache-dir .

USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health', timeout=3)"
CMD ["storyboard", "serve", "--host", "0.0.0.0", "--port", "8000"]
