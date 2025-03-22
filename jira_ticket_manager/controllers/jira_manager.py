from jira import JIRA
import getpass
import os
import sys
import yaml

CONFIG_FILE = os.path.expanduser("~/.jira-cli-config.yaml")


class JiraManager:
    """Manages interactions with JIRA API."""

    def __init__(self, server=None, username=None,
                 api_token=None, config_file=CONFIG_FILE):
        self.server = server
        self.username = username
        self.api_token = api_token
        self.config_file = config_file
        self.jira = None

        # Try to load config if not provided
        if not all([server, username, api_token]):
            self._load_config()

        # Connect to Jira
        self._connect()

    def _load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, "r") as file:
                config = yaml.safe_load(file)
                self.server = config.get('server', self.server)
                self.username = config.get('username', self.username)
                self.api_token = config.get('api_token', self.api_token)
        except Exception as e:
            print(f"Failed to load configuration: {e}", file=sys.stderr)

    def _save_config(self):
        """Save configuration to file."""
        try:
            config = {
                'server': self.server,
                'username': self.username,
                'api_token': self.api_token
            }
            with open(self.config_file, "w") as file:
                yaml.dump(config, file)
            os.chmod(self.config_file, 0o600)  # Secure file permissions
        except Exception as e:
            print(f"Failed to save configuration: {e}", file=sys.stderr)

    def _connect(self):
        """Connect to JIRA server."""
        # Ensure credentials are provided
        if not all([self.server, self.username, self.api_token]):
            self._prompt_credentials()
        try:
            self.jira = JIRA(server=self.server,
                             basic_auth=(self.username, self.api_token))
            # Test connection
            self.jira.myself()
            print(f"Connected to JIRA server: {self.server}", file=sys.stderr)
        except Exception as e:
            print(f"Failed to connect to JIRA: {e}", file=sys.stderr)
            self._prompt_credentials()
            self._connect()

    def _prompt_credentials(self):
        """Prompt user for JIRA credentials."""
        print("JIRA credentials required:")
        self.server = input(
            "JIRA Server URL (e.g., https://your-domain.atlassian.net): ").strip() or self.server
        self.username = input("Username (email): ").strip() or self.username
        self.api_token = getpass.getpass(
            "API Token: ").strip() or self.api_token

    def list_tickets(self, jql=None, max_results=50):
        """List JIRA tickets."""
        if not jql:
            jql = "assignee = currentUser() ORDER BY created DESC"

        try:
            issues = self.jira.search_issues(jql, maxResults=max_results)

            if not issues:
                print("No issues found.", file=sys.stderr)
                return

            return issues
        except Exception as e:
            print(f"Failed to list tickets: {e}", file=sys.stderr)
            return

    def view_ticket(self, ticket_key):
        """View details of a specific JIRA ticket."""
        try:
            issue = self.jira.issue(ticket_key)
            if not issue:
                print(f"Ticket {ticket_key} not found.", file=sys.stderr)
                return
            return issue
        except Exception as e:
            print(f"Failed to view ticket: {e}", file=sys.stderr)
            return

    def create_ticket(self, ticket_data):
        """Create a JIRA ticket with provided data."""
        try:
            # Validate required fields
            required_fields = ['project', 'summary', 'issuetype']
            for field in required_fields:
                if field not in ticket_data:
                    print(f"Missing required field: {field}", file=sys.stderr)
                    return

            # Create the issue
            new_issue = self.jira.create_issue(fields=ticket_data)

            print(f"Success! Created {new_issue.key}")

            return new_issue

        except Exception as e:
            print(f"Failed to create ticket: {e}", file=sys.stderr)
            return
