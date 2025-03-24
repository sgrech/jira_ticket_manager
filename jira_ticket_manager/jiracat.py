from jira_ticket_manager.controllers.jira_manager import JiraManager
from jira_ticket_manager.controllers.app_config import AppConfig
from pprint import pprint
import argparse
import sys
import webbrowser
from rich.markdown import Markdown
from rich.console import Console


def setup_argument_parser():
    parser = argparse.ArgumentParser(
        description='Display JIRA Issue')
    parser.add_argument('issue_key',
                        help='JIRA issue key')
    parser.add_argument('--view',
                        choices=['terminal', 'browser'],
                        default='terminal',
                        help="View issue in terminal or browser")

    args = parser.parse_args()
    return args


def safe_append(metadata, key, value):
    if value:
        metadata.append(f"**{key}:** {value}")
    return metadata


def format_issue_as_markdown(issue):
    """Format Jira issue as markdown string."""
    markdown = f"# {issue.key}: {issue.fields.summary}\n\n"

    issue_metadata, user_metadata, date_metdata = [], [], []

    if issue.fields.status:
        issue_metadata.append(f"**Status:** {issue.fields.status.name}")
    if issue.fields.priority:
        issue_metadata.append(f"**Priority:** {issue.fields.priority.name}")
    if hasattr(issue.fields, 'parent') and issue.fields.parent:
        issue_metadata.append(f"**Parent:** {issue.fields.parent.key}")
    if issue.fields.issuetype:
        issue_metadata.append(f"**Type:** {issue.fields.issuetype.name}")
    if issue.fields.customfield_12432:
        brands = [brand.value for brand in issue.fields.customfield_12432]
        issue_metadata.append(f"**Brands:** {', '.join(brands)}")
    if issue.fields.labels:
        issue_metadata.append(f"**Labels:** {', '.join(issue.fields.labels)}")
    if issue.fields.creator:
        user_metadata.append(
            f"**Creator:** {issue.fields.creator.displayName}")
    if issue.fields.assignee:
        user_metadata.append(
            f"**Assignee:** {issue.fields.assignee.displayName}")
    if issue.fields.reporter:
        user_metadata.append(
            f"**Reporter:** {issue.fields.reporter.displayName}")
    if issue.fields.created:
        date_metdata.append(
            f"**Created:** {issue.fields.created.split('T')[0]}")
    if issue.fields.updated:
        date_metdata.append(
            f"**Updated:** {issue.fields.updated.split('T')[0]}")

    # Add metadata to markdown
    markdown += "## Metadata\n\n"
    markdown += '\n'.join(issue_metadata)
    markdown += '\n\n'
    markdown += '\n'.join(user_metadata)
    markdown += '\n\n'
    markdown += '\n'.join(date_metdata)
    markdown += '\n\n'

    # Add description
    if issue.fields.description:
        markdown += "## Description\n\n"
        # Make sure code blocks are properly formatted
        description = issue.fields.description
        # Convert Jira's {code} blocks to markdown code blocks
        if '{code' in description:
            import re
            description = re.sub(r'\{code(?::([^}]+))?\}(.*?)\{code\}',
                                 lambda m: f"```{m.group(1) or ''}\n{m.group(2)}\n```",
                                 description, flags=re.DOTALL)
        markdown += f"{description}\n\n"

    # Add comments
    if hasattr(issue.fields, 'comment'):
        markdown += "## Comments\n\n"
        for comment in issue.fields.comment.comments:
            author = comment.author.displayName if hasattr(
                comment.author, 'displayName') else "Unknown"
            created = comment.created.split('T')[0] if hasattr(
                comment, 'created') else "Unknown date"

            markdown += f"### {author} - {created}\n\n"
            markdown += f"{comment.body}\n\n---\n\n"

    return markdown


def main():
    try:
        app_config = AppConfig()
    except Exception as e:
        print(f"Failed to load configuration: {e}")
        sys.exit(1)

    args = setup_argument_parser()

    if args.view == 'browser':
        issue_url = f"{app_config.server}/browse/{args.issue_key}"
        webbrowser.open(issue_url)
        sys.exit(0)

    jira_manager = JiraManager()
    issue = jira_manager.fetch_issue(args.issue_key)
    markdown_text = format_issue_as_markdown(issue)

    # Display markdown in terminal using rich
    console = Console()
    markdown = Markdown(markdown_text)
    console.print(markdown)


if __name__ == '__main__':
    main()
