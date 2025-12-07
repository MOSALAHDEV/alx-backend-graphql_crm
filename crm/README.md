# CRM Celery Report Task

## Requirements
- Redis running on `redis://localhost:6379/0`
- Python dependencies installed

## Setup

### 1) Install Redis (Ubuntu/Debian)
```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
```

### 2) Install dependencies
```bash
pip install -r requirements.txt
```

### 3) Run migrations
```bash
python manage.py migrate
```

### 4) Start Django server (GraphQL endpoint)
```bash
python manage.py runserver 0.0.0.0:8000
```

### 5) Start Celery worker
```bash
celery -A crm worker -l info
```

### 6) Start Celery Beat
```bash
celery -A crm beat -l info
```

## Verify
```bash
tail -n 20 /tmp/crm_report_log.txt
```

Expected format:
`YYYY-MM-DD HH:MM:SS - Report: X customers, Y orders, Z revenue`
