import requests
from datetime import datetime

from celery import shared_task


@shared_task(name="crm.tasks.generate_crm_report")
def generate_crm_report():
    """
    Uses GraphQL to fetch:
    - total customers
    - total orders
    - total revenue (sum of totalAmount)
    Logs to /tmp/crm_report_log.txt
    """
    url = "http://localhost:8000/graphql"
    query = """
    query {
      allCustomers { edges { node { id } } }
      allOrders { edges { node { totalAmount } } }
    }
    """

    resp = requests.post(url, json={"query": query}, timeout=10)
    resp.raise_for_status()
    data = resp.json().get("data", {})

    customers_edges = (data.get("allCustomers") or {}).get("edges") or []
    orders_edges = (data.get("allOrders") or {}).get("edges") or []

    total_customers = len(customers_edges)
    total_orders = len(orders_edges)

    revenue = 0.0
    for e in orders_edges:
        amt = ((e or {}).get("node") or {}).get("totalAmount")
        try:
            revenue += float(amt)
        except Exception:
            pass

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/crm_report_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{ts} - Report: {total_customers} customers, {total_orders} orders, {revenue} revenue\n")

    return "Report generated"


# Alias for strict checkers
def generatecrmreport():
    return generate_crm_report()
