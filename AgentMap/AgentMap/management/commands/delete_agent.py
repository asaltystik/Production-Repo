from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from AgentMap.models import LicensedState


# Creates a custom Django management command
# to delete licenses for a specified agent
# gets ran by the command python manage.py delete_agent <username>
class Command(BaseCommand):
    # This is the help message that will be displayed when the user runs the command with the --help flag
    help = ("Deletes all licenses for a specific agent, Helps to clean up "
            "the database when an agent leaves the company")

    # Add the username argument. This is the username of the agent to delete licenses for.
    # This is required to run the command
    def add_arguments(self, parser):
        parser.add_argument('username', type=str, help='Username of the agent to delete licenses for')

    # Handle method that is called when the management command is ran
    def handle(self, *args, **options):
        # Get the username
        try:  # Try to get the username using the argument
            user = User.objects.get(username=options['username'])
        except User.DoesNotExist:  # If the user does not exist, print an error message and return
            self.stdout.write(f"User with username {options['username']} does not exist.")
            return 1  # Return 1 to indicate an error

        # Query the LicensedState model for any licenses for the agent
        agent_licenses = LicensedState.objects.filter(agent=user.agent)

        # Iterate over the licenses and delete them
        for agent_license in agent_licenses:
            self.stdout.write(f'License {agent_license.licenseNumber} '  # print the license number
                              f'for agent {agent_license.agent.user.username}'  # print the username
                              f' in state {agent_license.state}'  # print the state
                              f' has been deleted.')
            agent_license.delete()  # Delete the license

        # print the number of licenses deleted
        self.stdout.write(f'{len(agent_licenses)}'
                          f' licenses deleted for {user.username}')  # Print the name
        return 0  # Return 0 to indicate success
