FROM python:3.13-alpine

RUN addgroup -S appgroup && adduser -S appuser -G appgroup

USER appuser

WORKDIR /app

COPY . /app

RUN pip install -r requirements.txt

HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 CMD curl -f http://localhost:5000/ || exit 1

HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:5000/ || exit 1

CMD ["python", "app.py"]


