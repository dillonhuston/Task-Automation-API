import requests
from app.config import Config


#TODO add pydantic schemas


class ClientPollServices:

    def __init__(self, config: Config):
        self.config = config
        self._token = None

    def signup(self,email, password, username):
        data = {"email": email, "password": password, "username": username}
        r = requests.post(f"{self.config.HOST}/auth/register", json=data)
        print(r.json())

    def login(self, email, password):
        data = {"username": email, "password": password}  
        r = requests.post(f"{self.config.HOST}/auth/login", data=data)
        resp = r.json()
        token = resp.get("access_token")
        self._token = token

        if not token:
            print("Login failed:", resp)
            return None
        print(f"Token: {token}")

        # Save token to the same path your client uses
        with open(self.config.TOKEN_FILE, "w") as f:
            f.write(token)
        print(f"Token saved to {self.config.TOKEN_FILE}")
        return token


    def create_task(self,task_type, schedule_time, receiver_email, title):
        print("Creating task")
        if not self._token:
            try:
                with open(str(self.config.TOKEN_FILE)) as f:
                    self._token = f.read().strip()
                    print("Found token locally.")
            except FileNotFoundError:
                print("Token file not found. Please log in first.")
                return

        headers = {"Authorization": f"Bearer {self._token}"}
        payload = {
            "task_type": task_type,
            "schedule_time": schedule_time,
            "receiver_email": receiver_email,
            "title": title
        }

        # Why am i defining this?

        url = f"{self.config.HOST}/schedule"

        try:
            r = requests.post(url, json=payload, headers=headers, timeout=10)  # 10-second timeout
        except requests.exceptions.Timeout:
            print("Request timed out. The server may be down or unreachable.")
            return
        except requests.exceptions.RequestException as e:
            print("Error sending request:", e)
            return

        try:
            resp = r.json()
            # add real error eception using custom exceptions 
        except Exception:
            resp = r.text  # fallback

        if r.status_code == 200:
            print("Task scheduled successfully")
        else:
            print("Failed to schedule task:", r.status_code, resp)
