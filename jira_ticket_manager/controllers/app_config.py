import yaml
import os

CONFIG_FILE = os.path.expanduser("~/.jira-cli-config.yaml")


class AppConfig:
    """Manages application configuration."""

    def __init__(self, config_file=None):
        if not config_file:
            config_file = CONFIG_FILE
        with open(config_file, "r") as file:
            config = yaml.safe_load(file)
            self.server = config.get('server')
            self.username = config.get('username')
            self.api_token = config.get('api_token')
            self.default_project = config.get('default_project')
            self.default_assignee = config.get('default_assignee')
            self.max_results = config.get('max_results', 50)

    def __str__(self):
        return f"server: {self.server}, username: {self.username}, api_token: {self.api_token}, default_project: {self.default_project}, default_assignee: {self.default_assignee}, max_results: {self.max_results}"
