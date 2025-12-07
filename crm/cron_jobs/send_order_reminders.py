#!/usr/bin/env python3
from datetime import datetime, timedelta, timezone

try:
    from gql import gql, Client
    from gql.transport.requests import RequestsHTTPTransport
except Exception as e:
    raise SystemExit(
        "Missing dependency: gql. Install with: pip install 'gql[requests]'"
    ) from e


GRAPHQL_URL = "http://localhost:8000/graphql"
LOG_FILE = "/tmp/order_reminders_log.txt"


def main() -> None:
    since = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()

    transport = RequestsHTTPTransport(url=GRAPHQL_URL, verify=True, retries=3)
    client = Client(transport=transport, fetch_schema_from_transport=False)

    query = gql(
        """
        query($since: DateTime!) {
          allOrders(filter: { orderDateGte: $since }) {
            edges {
              node {
                id
                orderDate
                customer {
                  email
                }
              }
            }
          }
        }
        """
    )

    result = client.execute(query, variable_values={"since": since})
    edges = (result.get("allOrders") or {}).get("edges") or []

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        for edge in edges:
            node = (edge or {}).get("node") or {}
            order_id = node.get("id")
            customer = node.get("customer") or {}
            email = customer.get("email")
            f.write(f"{ts} - Order {order_id} reminder sent to {email}\n")

    print("Order reminders processed!")


if __name__ == "__main__":
    main()
