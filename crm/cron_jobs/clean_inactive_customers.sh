#!/bin/bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "$0")/../.." && pwd)"

if [ -x "$PROJECT_ROOT/venv/bin/python" ]; then
  PYTHON="$PROJECT_ROOT/venv/bin/python"
else
  PYTHON="python3"
fi

DELETED_COUNT="$(
  cd "$PROJECT_ROOT"
  "$PYTHON" manage.py shell -c "from django.utils import timezone; from datetime import timedelta; from crm.models import Customer; cutoff=timezone.now()-timedelta(days=365); ids=list(Customer.objects.exclude(orders__order_date__gte=cutoff).values_list('id', flat=True).distinct()); count=len(ids); Customer.objects.filter(id__in=ids).delete(); print(count)"
)"

echo "$(date '+%Y-%m-%d %H:%M:%S') - Deleted ${DELETED_COUNT} inactive customers" >> /tmp/customer_cleanup_log.txt
