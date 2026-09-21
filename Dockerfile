FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

ARG APP_VERSION=7.8
ENV APP_VERSION=$APP_VERSION
ENV ENVIRONMENT=PRODUCTION

EXPOSE 5000

CMD ["python", "app.py"]