from datetime import datetime

from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport


def log_crm_heartbeat():
    """
    Appends a heartbeat line to /tmp/crm_heartbeat_log.txt in the format:
    DD/MM/YYYY-HH:MM:SS CRM is alive

    Also queries GraphQL hello field to verify the endpoint is responsive.
    """
    # Optional GraphQL check (doesn't block logging if it fails)
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
