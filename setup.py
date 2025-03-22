from setuptools import setup, find_packages

setup(
    name="jira_ticket_manager",
    version="0.1",
    packages=find_packages(),
    install_requires=['jira', 'PyYAML', 'prettytable'],
    entry_points={
        'console_scripts': [
            'jirals=jira_ticket_manager.jirals:main',
        ],
    },
    description="A simple tool to manage JIRA tickets",
    author="Shane Grech",
    author_email="shanegrech@gmail.com",
    url="https://github.com/sgrech/jira-ticket-manager",
)
