# CRM Celery Report Task

## Install Redis and dependencies

### Install Redis
```bash
sudo apt update
sudo apt install -y redis-server
sudo systemctl enable --now redis-server
```

### Install Python dependencies
```bash
pip install -r requirements.txt
```

## Run migrations
```bash
python manage.py migrate
```

## Start Celery worker
```bash
celery -A crm worker -l info
```

## Start Celery Beat
```bash
celery -A crm beat -l info
```

## Verify logs
```bash
tail -n 20 /tmp/crm_report_log.txt
```
