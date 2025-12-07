from datetime import datetime

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    """
    Appends a heartbeat line to /tmp/crm_heartbeat_log.txt:
    DD/MM/YYYY-HH:MM:SS CRM is alive

    Also queries GraphQL hello field to verify endpoint is responsive.
    """
    try:
        transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=True, retries=2)
        client = Client(transport=transport, fetch_schema_from_transport=False)
        query = gql("{ hello }")
        client.execute(query)
    except Exception:
        pass

    ts = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    with open("/tmp/crm_heartbeat_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{ts} CRM is alive\n")


def update_low_stock():
    """
    Runs GraphQL mutation UpdateLowStockProducts and logs results to:
    /tmp/low_stock_updates_log.txt
    """
    transport = RequestsHTTPTransport(url="http://localhost:8000/graphql", verify=True, retries=3)
    client = Client(transport=transport, fetch_schema_from_transport=False)

    mutation = gql(
        """
        mutation {
          updateLowStockProducts {
            message
            products {
              name
              stock
            }
          }
        }
        """
    )

    result = client.execute(mutation)
    payload = result.get("updateLowStockProducts") or {}
    products = payload.get("products") or []

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open("/tmp/low_stock_updates_log.txt", "a", encoding="utf-8") as f:
        for p in products:
            f.write(f"{ts} - {p.get('name')} restocked to {p.get('stock')}\n")
