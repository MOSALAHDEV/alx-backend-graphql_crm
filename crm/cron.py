from datetime import datetime

def log_crm_heartbeat():
    """
    Appends a heartbeat line to /tmp/crm_heartbeat_log.txt in the format:
    DD/MM/YYYY-HH:MM:SS CRM is alive
    """
    ts = datetime.now().strftime("%d/%m/%Y-%H:%M:%S")
    with open("/tmp/crm_heartbeat_log.txt", "a", encoding="utf-8") as f:
        f.write(f"{ts} CRM is alive\n")
