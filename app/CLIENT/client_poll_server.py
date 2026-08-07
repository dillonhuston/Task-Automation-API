import asyncio
import time
from datetime import datetime
from typing import Optional

import httpx

from app.config import Config
from app.Database.DatabaseOperations import DatabaseOperations
from app.dependencies.constants import TASK_STATUS_SCHEDULED
from app.models.database import AsyncSessionLocal
from app.tasks.tasks import file_cleanup


class ClientPollServer:
    def __init__(self, config: Config):
        self.config = config
        self.db_ops = DatabaseOperations()

    def load_token(self) -> Optional[str]:
        try:
            with open(self.config.TOKEN_FILE) as f:
                return f.read().strip()
        except FileNotFoundError:
            print("[ERROR] Token file not found.")
            return None

    async def show_task_history(self, limit: int = 5):
        async with AsyncSessionLocal() as db:
            histories = await self.db_ops.ReturnAllTaskHistory(db, limit)
            if histories:
                print("\n--- Task History (Last {} Executions) ---".format(limit))
                print(f"{'Task Type':<15} {'Status':<10} {'Executed At':<20} {'Details'}")
                for h in histories:
                    executed = h.executed_at.strftime("%Y-%m-%d %H:%M")
                    print(f"{h.task_type:<15} {h.status:<10} {executed:<20} {h.details}")

    async def poll_server(self):
        token = self.load_token()
        if not token:
            return

        headers = {"Authorization": f"Bearer {token}"}
        print("[INFO] Starting async task polling loop...")

        async with httpx.AsyncClient(timeout=10.0) as client:
            while True:
                try:
                    response = await client.get(f"{self.config.HOST}/list_tasks", headers=headers)
                    if response.status_code != 200:
                        print(f"[ERROR] Server returned {response.status_code}: {response.text}")
                        await asyncio.sleep(float(self.config.POLL_INTERVAL))
                        continue

                    tasks = response.json()
                    if not tasks:
                        print("[INFO] No tasks available.")
                        await asyncio.sleep(float(self.config.POLL_INTERVAL))
                        continue

                    print("\n--- Retrieved Tasks ---")
                    for task in tasks:
                        task_id = task.get("id")
                        task_type = task.get("task_type")
                        status = task.get("status")
                        receiver_email = task.get("receiver_email")
                        schedule_time_str = task.get("schedule_time")

                        print(f"→ ID {task_id} | Type {task_type} | Status {status}")

                        if task_type != "file_cleanup" or status not in (TASK_STATUS_SCHEDULED,):
                            continue

                        if not schedule_time_str:
                            print(f"[WARN] Task {task_id} has no schedule_time set.")
                            continue

                        schedule_time = datetime.fromisoformat(schedule_time_str)
                        now = datetime.now()

                        if now >= schedule_time:
                            print(f"[EXECUTE] Running task {task_id}")
                            try:
                                await asyncio.to_thread(file_cleanup, task_id, receiver_email)
                            except Exception as e:
                                print(f"[ERROR] Failed to execute task {task_id}: {e}")
                        else:
                            time_left = (schedule_time - now).total_seconds()
                            print(f"[WAIT] Task {task_id} runs in {int(time_left)}s")

                    await self.show_task_history(limit=5)

                except httpx.RequestError as e:
                    print(f"[ERROR] Connection issue: {e}")
                except Exception as e:
                    print(f"[ERROR] Unexpected error: {e}")

                await asyncio.sleep(float(self.config.POLL_INTERVAL))


if __name__ == "__main__":
    config = Config()
    poller = ClientPollServer(config)
    asyncio.run(poller.poll_server())