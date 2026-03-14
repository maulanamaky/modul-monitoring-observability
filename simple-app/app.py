import os
import time
import random
import logging
import mysql.connector
from flask import Flask, jsonify, request
from prometheus_client import Counter, Histogram, Gauge, generate_latest, CONTENT_TYPE_LATEST

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s'
)
logger = logging.getLogger(__name__)

app = Flask(__name__)

REQUEST_COUNT = Counter(
    'app_request_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)
REQUEST_LATENCY = Histogram(
    'app_request_duration_seconds',
    'HTTP request duration',
    ['endpoint']
)
DB_QUERY_COUNT = Counter(
    'app_db_query_total',
    'Total DB queries',
    ['operation', 'status']
)
ACTIVE_USERS = Gauge(
    'app_active_users',
    'Simulated active users'
)

def get_db():
    return mysql.connector.connect(
        host=os.getenv('MYSQL_HOST', 'mysql'),
        user=os.getenv('MYSQL_USER', 'appuser'),
        password=os.getenv('MYSQL_PASSWORD', 'apppassword'),
        database=os.getenv('MYSQL_DATABASE', 'appdb')
    )

def init_db():
    for attempt in range(10):
        try:
            conn = get_db()
            cur = conn.cursor()
            cur.execute("""
                CREATE TABLE IF NOT EXISTS visits (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    path VARCHAR(255),
                    visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()
            cur.close(); conn.close()
            logger.info("Database initialized successfully")
            return
        except Exception as e:
            logger.warning(f"DB not ready (attempt {attempt+1}/10): {e}")
            time.sleep(3)
    logger.error("Failed to initialize database after 10 attempts")

@app.route('/')
def index():
    start = time.time()
    try:
        conn = get_db()
        cur = conn.cursor()
        cur.execute("INSERT INTO visits (path) VALUES (%s)", (request.path,))
        conn.commit()
        cur.execute("SELECT COUNT(*) FROM visits")
        count = cur.fetchone()[0]
        cur.close(); conn.close()

        ACTIVE_USERS.set(random.randint(5, 50))
        DB_QUERY_COUNT.labels(operation='insert', status='success').inc()
        REQUEST_COUNT.labels(method='GET', endpoint='/', status='200').inc()
        logger.info(f"GET / — total visits: {count}")
        return jsonify({"message": "Hello from Flask App!", "total_visits": count})
    except Exception as e:
        DB_QUERY_COUNT.labels(operation='insert', status='error').inc()
        REQUEST_COUNT.labels(method='GET', endpoint='/', status='500').inc()
        logger.error(f"Error on GET /: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        REQUEST_LATENCY.labels(endpoint='/').observe(time.time() - start)

@app.route('/slow')
def slow():
    start = time.time()
    delay = random.uniform(0.5, 3.0)
    time.sleep(delay)
    REQUEST_COUNT.labels(method='GET', endpoint='/slow', status='200').inc()
    REQUEST_LATENCY.labels(endpoint='/slow').observe(time.time() - start)
    logger.warning(f"GET /slow — took {delay:.2f}s")
    return jsonify({"message": "This was a slow response", "delay_seconds": round(delay, 2)})

@app.route('/error')
def error():
    REQUEST_COUNT.labels(method='GET', endpoint='/error', status='500').inc()
    logger.error("GET /error — simulated error triggered")
    return jsonify({"error": "Simulated internal server error"}), 500

@app.route('/health')
def health():
    return jsonify({"status": "ok"})

@app.route('/metrics')
def metrics():
    return generate_latest(), 200, {'Content-Type': CONTENT_TYPE_LATEST}

if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000)
