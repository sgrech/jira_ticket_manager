from jira import JIRA
from jira_ticket_manager.controllers.app_config import AppConfig
import sys


class JiraManager:
    """Manages interactions with JIRA API."""

    def __init__(self, config_file=None):
        self.app_config = AppConfig(config_file)
        self.jira = None

        # Connect to Jira
        self._connect()

    def _connect(self):
        """Connect to JIRA server."""
        # Ensure credentials are provided
        if not all([
                self.app_config.server,
                self.app_config.username,
                self.app_config.api_token]):
            raise Exception("JIRA credentials not found in App Configuration.")
        try:
            self.jira = JIRA(
                server=self.app_config.server,
                basic_auth=(
                    self.app_config.username, self.app_config.api_token))
            # Test connection
            self.jira.myself()
            print(
                f"Connected to JIRA server: {self.app_config.server}",
                file=sys.stderr)
        except Exception as e:
            raise Exception(f"Failed to connect to JIRA: {e}")

    def list_issues(self, jql=None, max_results=50):
        """List JIRA issues."""
        if not jql:
            jql = "assignee = currentUser() ORDER BY created DESC"

        try:
            issues = self.jira.search_issues(jql, maxResults=max_results)

            if not issues:
                print("No issues found.", file=sys.stderr)
                return

            return issues
        except Exception as e:
            print(f"Failed to list issues: {e}", file=sys.stderr)
            return

    def fetch_issue(self, issue_key):
        """View details of a specific JIRA issue."""
        try:
            issue = self.jira.issue(issue_key)
            if not issue:
                print(f"Issue {issue_key} not found.", file=sys.stderr)
                return
            return issue
        except Exception as e:
            print(f"Failed to view issue: {e}", file=sys.stderr)
            return

    def create_issue(self, issue_data):
        """Create a JIRA issue with provided data."""
        try:
            # Validate required fields
            required_fields = ['project', 'summary', 'issuetype']
            for field in required_fields:
                if field not in issue_data:
                    print(f"Missing required field: {field}", file=sys.stderr)
                    return

            # Create the issue
            new_issue = self.jira.create_issue(fields=issue_data)

            print(f"Success! Created {new_issue.key}")

            return new_issue

        except Exception as e:
            print(f"Failed to create issue: {e}", file=sys.stderr)
            return
