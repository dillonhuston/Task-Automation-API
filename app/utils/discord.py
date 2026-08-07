import requests
from typing import Optional
from datetime import datetime, UTC
from app.utils.logger import SingletonLogger

logger = SingletonLogger().get_logger()

def send_discord_notification(status: str, message: str, task_name: str, webhook_url: str,color: Optional[int] = None):
    try:
        if color is None:
            status_colors = {
                "SCHEDULED": 0x3498db,
                "COMPLETED": 0x2ecc71,
                "FAILED": 0xe74c3c,
                "PENDING": 0xf1c40f,
            }
            color = status_colors.get(status.upper(), 0x808080)

        embed = {
            "title": f"Task Update: {task_name}",
            "description": message,
            "color": color,
            "timestamp": datetime.now(UTC).isoformat(),  
            "fields": [
                {"name": "Status", "value": status, "inline": True},
                {"name": "Task Name", "value": task_name, "inline": True}
            ],

            "footer": {"text": "Task Automation API"},
        }

        payload = {"content": None, "embeds": [embed]}
        response = requests.post(webhook_url, json=payload)
        if response.status_code == 204:
            return f"Embed sent for task {task_name}"
        else:
            logger.error(f"Discord embed failed: {response.text}")
    except Exception as e:
        logger.error(f"Error sending Discord embed: {e}")
    return None