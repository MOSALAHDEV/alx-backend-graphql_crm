#!/bin/bash
set -euo pipefail

BASE_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
cd "$BASE_DIR"

deleted_count="$(
python3 manage.py shell -c "
from datetime import timedelta
from django.utils import timezone
from django.db.models import Max, Q
from crm.models import Customer, Order

cutoff = timezone.now() - timedelta(days=365)

fk = next(
    f for f in Order._meta.fields
    if getattr(f, 'related_model', None) == Customer
)
rel = fk.related_query_name()

qs = Customer.objects.annotate(last_order=Max(f'{rel}__order_date'))
inactive = qs.filter(Q(last_order__lt=cutoff) | Q(last_order__isnull=True))

count = inactive.count()
inactive.delete()
print(count)
" 2>/dev/null | tail -n 1
)"

ts="$(date '+%Y-%m-%d %H:%M:%S')"
echo "${ts} Deleted customers: ${deleted_count}" >> /tmp/customer_cleanup_log.txt

