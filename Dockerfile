FROM python:3.12-slim

# Untuk mencegah python bikin .pyc bytecode cache files
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 

WORKDIR /app

COPY requirements.txt ./
RUN python -m pip install --no-cache-dir -r requirements.txt

# ini idnya bebas apa aja
RUN groupadd --gid 1000 app \
    && useradd --uid 1000 --gid app --create-home app \
    && mkdir -p /app/output \
    && chown app:app /app/output

COPY --chown=app:app src/ ./src/

USER app

EXPOSE 8080

CMD ["python", "src/main.py"]
