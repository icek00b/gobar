FROM python:3.13-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .
COPY templates/ templates/
COPY static/ static/
COPY hosts.yaml hosts.yaml

ENV GOBAR_HOST=0.0.0.0 \
    GOBAR_PORT=5000

EXPOSE 5000

CMD ["python", "app.py"]
