FROM python:3.11-slim AS builder

WORKDIR /install

COPY requirements.txt .

RUN pip install --upgrade pip \
 && pip install \
      --target=/install/packages \
      --no-cache-dir \
      -r requirements.txt


FROM python:3.11-alpine AS runtime

RUN apk add --no-cache libstdc++


COPY --from=builder /install/packages /usr/local/lib/python3.11/site-packages

WORKDIR /app
COPY app.py .

RUN adduser -D appuser
USER appuser

EXPOSE 5000

CMD ["python", "app.py"]