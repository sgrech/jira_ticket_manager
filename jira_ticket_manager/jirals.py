from datetime import datetime
from jira_ticket_manager.controllers.jira_manager import JiraManager
from prettytable import PrettyTable
import argparse
import sys
import textwrap
import os
import yaml

CONFIG_FILE = os.path.expanduser("~/.jira-cli-config.yaml")


def main():
    try:
        with open(CONFIG_FILE, "r") as file:
            config = yaml.safe_load(file)
            default_project = config.get('default_project', None)
    except Exception as e:
        print(f"Failed to load configuration: {e}", file=sys.stderr)
        sys.exit(1)

    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description='Filter and list JIRA tickets')
    parser.add_argument('--jql', help='JIRA Query Language to filter tickets')
    parser.add_argument('--max', type=int, default=50,
                        help='Maximum number of tickets to display')
    parser.add_argument('--my-tickets', action='store_true',
                        help='Show only tickets assigned to me')
    parser.add_argument('--my-reported', action='store_true',
                        help='Show only tickets reported by me')
    parser.add_argument(
        '--project', help='Filter by project key', default=default_project)
    parser.add_argument(
        '--status', help='Comma separated list of statuses (e.g. "To Do, In Progress")')
    parser.add_argument(
        '--ne-status', help='Comma separated list of statuses to exclude (e.g. "Done, Resolved")')
    parser.add_argument(
        '--tags', help='Comma separated list of tags (e.g. "bug, enhancement")')

    # Parse the arguments
    args = parser.parse_args()

    # Create a JiraManager instance
    jira_manager = JiraManager()

    # Build JQL from args
    jql_parts = []

    if args.my_tickets:
        jql_parts.append('assignee = currentUser()')
    if args.my_reported:
        jql_parts.append('reporter = currentUser()')
    if args.project:
        jql_parts.append(f'project = {args.project}')
    if args.status:
        statues = args.status.split(',')
        jql_parts.append('status IN ({})'.format(
            ', '.join([f'"{status.strip()}"' for status in statues]))
        )
    if args.ne_status:
        statues = args.ne_status.split(',')
        jql_parts.append('status NOT IN ({})'.format(
            ', '.join([f'"{status.strip()}"' for status in statues]))
        )
    if args.tags:
        tags = args.tags.split(',')
        jql_parts.append('labels IN ({})'.format(
            ', '.join([f'"{tag.strip()}"' for tag in tags]))
        )
    # Combine or used provided JQL
    if jql_parts and not args.jql:
        jql = ' AND '.join(jql_parts) + " ORDER BY created DESC"
    else:
        jql = args.jql

    # Get the tickets
    try:
        issues = jira_manager.list_tickets(jql, args.max)
        if not issues:
            print('No issues found matching your criteria.', file=sys.stderr)

        table = PrettyTable()

        table.field_names = ["Key", "Created", "Updated", "Assignee",
                             "Status", "Priority", "Summary", "Tags"]
        table.align = 'l'
        table.max_width = 120

        for issue in issues:
            # Formate dates
            date_format = "%Y-%m-%dT%H:%M:%S"
            output_date_format = "%Y-%m-%d %H:%M"
            created = datetime.strptime(issue.fields.created[:19], date_format)
            create_str = created.strftime(output_date_format)
            updated = datetime.strptime(issue.fields.updated[:19], date_format)
            updated_str = updated.strftime(output_date_format)

            # Concatenate tags
            tags = ''
            if hasattr(issue.fields, 'labels') and issue.fields.labels:
                tags = ', '.join(issue.fields.labels)

            # Set assignee
            assignee = issue.fields.assignee.displayName if issue.fields.assignee else 'Unassigned'

            # Set priority
            priority = issue.fields.priority.name if issue.fields.priority else 'N/A'

            # Set short summary
            summary = textwrap.shorten(
                issue.fields.summary, width=50, placeholder='...')

            table.add_row([issue.key, create_str, updated_str, assignee,
                           issue.fields.status.name, priority, summary, tags])

        print(table)
        print(f'\nTotal issues: {len(issues)}', file=sys.stderr)

    except Exception as e:
        print(f'Failed to get tickets: {e}', file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
