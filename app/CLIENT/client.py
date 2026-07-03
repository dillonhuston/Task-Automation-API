import argparse
from  services import ClientPollServices # handles API calls
from dateutil import parser as dateparser
from datetime import timezone
from app.config import Config


def parse_time(user_input: str) -> str:
    try:
        dt = dateparser.parse(user_input)
        if not dt:
            raise ValueError("Could not parse date/time.")
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.isoformat()
    except Exception as e:
        print(f"Invalid time format: {e}")
        print("Try formats like '2025-10-22 19:00', '22/10/2025 7pm', or 'Oct 22 7pm'.")
        exit(1)

def main(clientservice: ClientPollServices):
    parser = argparse.ArgumentParser(
        prog="Task Automation CLI",
        description="Client for Task Automation API"
    )
    subparser = parser.add_subparsers(dest="command", required=True)

    # Signup
    signup = subparser.add_parser("signup", help="Signup with username, email, and password")
    signup.add_argument("--email", required=True)
    signup.add_argument("--password", required=True)
    signup.add_argument("--username", required=True)


    # Login
    login = subparser.add_parser("login", help="Login with email and password")
    login.add_argument("--email", required=True)
    login.add_argument("--password", required=True)

    # Create Task
    create_task = subparser.add_parser("create_task", help="Create a new task (reminder or file_cleanup)")
    create_task.add_argument("--task_type", type=str, choices=["reminder", "file_cleanup"])
    create_task.add_argument("--schedule_time", type=str, help="Time (e.g. '2025-10-22 19:00' or 'tomorrow 7pm')")
    create_task.add_argument("--receiver_email", type=str)
    create_task.add_argument("--title", type=str, required=True, help="Title of the task")


    args = parser.parse_args()

    # Handle commands
    if args.command == "signup":
        clientservice.signup(args.email, args.password, args.username)

    elif args.command == "login":
        clientservice.login( args.email, args.password)

    elif args.command == "create_task":
        iso_time = parse_time(args.schedule_time)
        clientservice.create_task(args.task_type, iso_time, args.receiver_email, args.title)


if __name__ == "__main__":
    config = Config()
    clientservices = ClientPollServices(config)
    main(clientservices)
