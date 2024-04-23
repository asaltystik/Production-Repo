from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from AgentMap.models import LicensedState


# Creates a custom Django management command to check the LicensedState model
# for any licenses past their expiration date and deletes them
# This will probably be running as a nightly cron job
class Command(BaseCommand):

    # This is the help message that will be displayed when the user runs the command with the --help flag
    help = ('Checks the LicensedState model for any licenses past their'
            ' expiration date and deletes them')

    # Handle method that is called when the management command is ran
    def handle(self, *args, **kwargs):
        # Get the current date
        current_date = timezone.now().date()

        # Query the LicensedState model for any licenses past their expiration date
        expired_licenses = LicensedState.objects.filter(expiration__lt=current_date)

        # Dictionary to store the licenses that will be deleted
        agent_licenses = {}  # This is empty for now

        # Iterate over the expired licenses and delete them
        for expired_license in expired_licenses:
            # Print the expired license
            self.stdout.write(f'License {expired_license.licenseNumber} '  # This is the license number
                              f'for agent {expired_license.agent.user.username}'  # This is the agent username
                              f' in state {expired_license.state}'  # This is the state abbreviation
                              f' has expired and will be deleted.')

            # Add the license to the dictionary
            agent_email = expired_license.agent.user.email

            # Check if the agent is already in the dictionary
            if agent_email not in agent_licenses:
                agent_licenses[agent_email] = []  # Creates a list for the agent if it doesn't exist
            agent_licenses[agent_email].append(f'License {expired_license.licenseNumber}'  # This is the license number
                                               f' in state {expired_license.state}\n')  # add the license to the list

            # Delete the license
            expired_license.delete()  # Delete this shit quay

        # Print the number of expired licenses deleted
        print(f'{len(expired_licenses)} expired licenses deleted.')

        # Send email to each agent with their deleted licenses
        for agent_email, agent_license in agent_licenses.items():
            send_mail(
                'Expired License Deletion Notice',  # This is the subject of the email
                f'The following licenses have expired and been deleted:\n'
                f'{"".join(agent_license)}'  # This is the string of all deleted licenses
                f'Please contact Steve or Craig to renew your licenses.',
                'carick@securecare65.com',  # We are sending this from my personal work email
                [agent_email],  # This is the agents email address
                fail_silently=False,  # This will raise an exception if the email fails to send
            )  # send the email to the agent notifying them of the deletion.

        # Print the number of agents notified
        print(f'{len(agent_licenses)} agents notified of expired licenses.')
        # print the names of the agents that were notified
        print(f'Agents notified:\n {"\n".join(agent_licenses.keys())}\n')
