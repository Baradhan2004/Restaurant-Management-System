FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV RESTAURANT_DB=/data/restaurant.db
RUN mkdir -p /data
EXPOSE 5000
CMD ["sh", "-c", "python -c 'import app; app.init_db()' && gunicorn --bind 0.0.0.0:5000 app:app"]
