from jira_ticket_manager.lib.JiraManager import JiraManager

if __name__ == "__main__":
    manager = JiraManager()
    print(manager.list_tickeets())
