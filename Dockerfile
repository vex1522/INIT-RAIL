FROM python:3.11-slim

LABEL maintainer="Team SetA"
LABEL description="Chennai Suburban Rail Traffic Analysis Dashboard"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p data outputs

EXPOSE 5000

ENV FLASK_ENV=production

CMD ["gunicorn", "-w", "2", "-b", "0.0.0.0:5000", "--timeout", "120", "app:app"]
