#!/usr/bin/env python3
"""
JIRA Ticket Manager - A command-line interface for managing JIRA issues.

Features:
1. List JIRA issues based on filters
2. View individual issue details
3. Create JIRA issues from YAML templates
"""

import argparse
import os
# import sys
import yaml
from prettytable import PrettyTable
from jira import JIRA
import getpass
import textwrap
from datetime import datetime

# Constants
CONFIG_FILE = os.path.expanduser("~/.jira-cli-config.yaml")


class JiraManager:
    """Manages interactions with JIRA API."""

    def __init__(self, server=None, username=None, api_token=None, config_file=CONFIG_FILE):
        """Initialize with JIRA credentials."""
        self.config_file = config_file
        self.server = server
        self.username = username
        self.api_token = api_token
        self.jira = None

        # Try to load config if not provided
        if not all([server, username, api_token]):
            self._load_config()

        # Connect to JIRA
        self._connect()

    def _load_config(self):
        """Load configuration from file."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as file:
                    config = yaml.safe_load(file)
                    self.server = config.get('server', self.server)
                    self.username = config.get('username', self.username)
                    self.api_token = config.get('api_token', self.api_token)
        except Exception as e:
            print(f"Error loading config: {e}")

    def _save_config(self):
        """Save configuration to file."""
        try:
            config = {
                'server': self.server,
                'username': self.username,
                'api_token': self.api_token
            }
            with open(self.config_file, 'w') as file:
                yaml.dump(config, file)
            os.chmod(self.config_file, 0o600)  # Secure permissions
        except Exception as e:
            print(f"Error saving config: {e}")

    def _connect(self):
        """Connect to JIRA server."""
        # Ensure we have credentials
        if not all([self.server, self.username, self.api_token]):
            self._prompt_credentials()

        try:
            self.jira = JIRA(server=self.server, basic_auth=(
                self.username, self.api_token))
            # Test connection
            self.jira.myself()
            print(f"Connected to JIRA at {self.server} as {self.username}")
        except Exception as e:
            print(f"Error connecting to JIRA: {e}")
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

        # Ask to save
        save = input(
            "Save credentials for future use? (y/n): ").lower().strip()
        if save == 'y':
            self._save_config()

    def list_issues(self, jql=None, max_results=50):
        """List JIRA issues based on JQL filter."""
        if not jql:
            jql = "assignee = currentUser() ORDER BY updated DESC"

        try:
            issues = self.jira.search_issues(jql, maxResults=max_results)

            if not issues:
                print("No issues found matching your criteria.")
                return

            table = PrettyTable()
            table.field_names = ["Key", "Created", "Updated", "Assignee",
                                 "Status", "Priority", "Summary", "Tags",
                                 "Link"]
            table.align = "l"
            table.max_width = 120

            for issue in issues:
                # Format date
                updated = datetime.strptime(
                    issue.fields.updated[:19], "%Y-%m-%dT%H:%M:%S")
                updated_str = updated.strftime("%Y-%m-%d %H:%M")

                created = datetime.strptime(
                    issue.fields.created[:19], "%Y-%m-%dT%H:%M:%S")
                created_str = created.strftime("%Y-%m-%d %H:%M")

                # Concatenate tags
                tags = ""
                if hasattr(issue.fields, 'labels') and issue.fields.labels:
                    tags = ", ".join(issue.fields.labels)

                assignee = issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'

                # Add row
                table.add_row([
                    issue.key,
                    created_str,
                    updated_str,
                    assignee,
                    issue.fields.status.name,
                    issue.fields.priority.name if hasattr(
                        issue.fields, 'priority') and issue.fields.priority else 'N/A',
                    textwrap.shorten(issue.fields.summary,
                                     width=60, placeholder="..."),
                    tags,
                    f"{self.server}/browse/{issue.key}"
                ])

            print(table)
            print(f"\nTotal issues: {len(issues)}")

        except Exception as e:
            print(f"Error listing issues: {e}")

    def view_issue(self, issue_key):
        """View details of a specific JIRA issue."""
        try:
            issue = self.jira.issue(issue_key)

            # Header
            print("\n" + "="*80)
            print(f"{issue.key}: {issue.fields.summary}")
            print("="*80)

            # Details table
            details = PrettyTable()
            details.field_names = ["Field", "Value"]
            details.align = "l"
            details.max_width = 60

            # Add fields
            details.add_row(["Status", issue.fields.status.name])
            details.add_row(["Priority", issue.fields.priority.name if hasattr(
                issue.fields, 'priority') and issue.fields.priority else 'N/A'])
            details.add_row(["Reporter", issue.fields.reporter.displayName])
            details.add_row(
                ["Assignee", issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'])
            details.add_row(["Created", issue.fields.created[:10]])
            details.add_row(["Updated", issue.fields.updated[:10]])

            # Add components if available
            if hasattr(issue.fields, 'components') and issue.fields.components:
                components = ", ".join(
                    [c.name for c in issue.fields.components])
                details.add_row(["Components", components])

            # Add fix versions if available
            if hasattr(issue.fields, 'fixVersions') and issue.fields.fixVersions:
                versions = ", ".join(
                    [v.name for v in issue.fields.fixVersions])
                details.add_row(["Fix Versions", versions])

            print(details)

            # Description
            print("\nDescription:")
            print("-"*80)
            if issue.fields.description:
                print(issue.fields.description)
            else:
                print("No description provided.")
            print("-"*80)

            # Comments
            if hasattr(issue.fields, 'comment') and issue.fields.comment.comments:
                print("\nComments:")
                for comment in issue.fields.comment.comments:
                    print("\n" + "-"*40)
                    print(
                        f"{comment.author.displayName} | {comment.created[:10]} {comment.created[11:16]}")
                    print("-"*40)
                    print(comment.body)

        except Exception as e:
            print(f"Error viewing issue {issue_key}: {e}")

    def create_issue(self, yaml_file):
        """Create a JIRA issue from YAML file."""
        try:
            # Load YAML file
            with open(yaml_file, 'r') as file:
                issue_data = yaml.safe_load(file)

            # Validate required fields
            required_fields = ['project', 'summary', 'issuetype']
            for field in required_fields:
                if field not in issue_data:
                    print(
                        f"Error: Missing required field '{field}' in YAML file")
                    return

            # Create the issue
            new_issue = self.jira.create_issue(fields=issue_data)

            print(f"Success! Created issue {new_issue.key}")

            # Offer to view the created issue
            view = input(
                f"View issue {new_issue.key}? (y/n): ").lower().strip()
            if view == 'y':
                self.view_issue(new_issue.key)

        except Exception as e:
            print(f"Error creating issue: {e}")


def main():
    """Main entry point for the CLI."""
    parser = argparse.ArgumentParser(description="JIRA Ticket Manager CLI")

    # Server and authentication options
    auth_group = parser.add_argument_group('Authentication')
    auth_group.add_argument('--server', help='JIRA server URL')
    auth_group.add_argument('--username', help='JIRA username (email)')
    auth_group.add_argument('--api-token', help='JIRA API token')

    # Subcommands
    subparsers = parser.add_subparsers(dest='command', help='Command')

    # List command
    list_parser = subparsers.add_parser('list', help='List JIRA issues')
    list_parser.add_argument('--jql', help='JQL query to filter issues')
    list_parser.add_argument(
        '--max', type=int, default=50, help='Maximum number of issues to display')

    # Common JQL shortcuts
    list_parser.add_argument(
        '--my-issues', action='store_true', help='Show issues assigned to me')
    list_parser.add_argument(
        '--my-reported', action='store_true', help='Show issues reported by me')
    list_parser.add_argument('--project', help='Filter by project key')
    list_parser.add_argument(
        '--status', help='Filter by status (e.g., "In Progress,Done")')
    list_parser.add_argument(
        '--ne-status', help='Filter by status not equal to (e.g., "Done,Resolved")')
    list_parser.add_argument(
        '--tags', help='Filter by tags (e.g., "bug,security")')

    # View command
    view_parser = subparsers.add_parser('view', help='View a JIRA issue')
    view_parser.add_argument(
        'issue_key', help='JIRA issue key (e.g., PROJ-123)')

    # Create command
    create_parser = subparsers.add_parser(
        'create', help='Create a JIRA issue from YAML file')
    create_parser.add_argument(
        'yaml_file', help='Path to YAML file with issue details')

    # Parse arguments
    args = parser.parse_args()

    # If no command is specified, show help
    if not args.command:
        parser.print_help()
        return

    # Initialize JIRA manager
    jira_manager = JiraManager(
        server=args.server,
        username=args.username,
        api_token=args.api_token
    )

    # Execute command
    if args.command == 'list':
        # Build JQL from args
        jql_parts = []

        if args.my_issues:
            jql_parts.append("assignee = currentUser()")
        if args.my_reported:
            jql_parts.append("reporter = currentUser()")
        if args.project:
            jql_parts.append(f"project = {args.project}")
        if args.status:
            statuses = args.status.split(",")
            jql_parts.append("status IN ({})".format(
                ", ".join([f'"{status}"' for status in statuses]))
            )
            # jql_parts.append(f"status = \"{args.status}\"")
        if args.ne_status:
            # jql_parts.append(f"status != \"{args.ne_status}\"")
            statuses = args.ne_status.split(",")
            jql_parts.append("status NOT IN ({})".format(
                ", ".join([f'"{status}"' for status in statuses]))
            )
        if args.tags:
            tags = args.tags.split(",")
            jql_parts.append("labels IN ({})".format(
                ", ".join([f'"{tag}"' for tag in tags]))
            )

        # Combine or use provided JQL
        if jql_parts and not args.jql:
            jql = " AND ".join(jql_parts) + " ORDER BY updated DESC"
        else:
            jql = args.jql

        jira_manager.list_issues(jql=jql, max_results=args.max)

    elif args.command == 'view':
        jira_manager.view_issue(args.issue_key)

    elif args.command == 'create':
        jira_manager.create_issue(args.yaml_file)


if __name__ == "__main__":
    main()
