from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.db.models import Count
from django.utils import timezone
from datetime import timedelta
from AgentMap.models import LicensedState, Agent


# This is a custom django management command that sends warning emails to agents
# Probably will be implemented as a cron job to run on the first of every month
# to warn agents of upcoming license expirations.
class Command(BaseCommand):

    # This is the help message that will be displayed when the user runs the command with the --help flag
    help = ("Warns agents of upcoming license expirations by sending an email"
            " to the agent's email address.")

    # Handle method that is called when the management command is ran.
    def handle(self, *args, **kwargs):
        # Get the current date and the last day of the current month
        current_date = timezone.now().date()  # Today's date
        end_date = current_date + timedelta(days=31)  # Doing 31 days to cover the 7 months with 31 days.
        # Ignoring the case of a leap year cause the next one is 4 years away.

        # Query the LicensedState model for any licenses expiring within the current month
        expiring_licenses = LicensedState.objects.filter(expiration__range=(current_date, end_date))

        # Group the results by agent and count the number of expiring licenses for each agent
        agents = expiring_licenses.values('agent').annotate(num_expiring=Count('id'))

        # For each unique agent, gather all their upcoming expirations and send an email
        for agent in agents:
            agent_obj = Agent.objects.get(id=agent['agent'])  # Create an agent object from the agent id
            # Filter the expiring licenses for the current agent
            agent_expirations = expiring_licenses.filter(agent=agent_obj)  # This is a queryset of all expiring licenses
            # Create a string of all upcoming expirations for the agent
            expirations_str = "\n".join([f"License {expiring_license.licenseNumber}"  # This is the license number
                                         f" in state {expiring_license.state}"  # This is the state abbreviation
                                         f" expires on {expiring_license.expiration.strftime('%m/%d/%Y')}"  # Date
                                         for expiring_license in agent_expirations])  # Loops through expiring licenses
            send_mail(
                'License Expiration Notice',  # This is the subject of the email
                f'You have {agent["num_expiring"]} license(s) expiring'  # agent["num_expiring"] returns the count
                f' this month:\n{expirations_str}',  # This is the string of all upcoming expirations
                'carick@securecare65.com',  # We are sending this from my personal work email
                [agent_obj.user.email],  # This is the agents email address
                fail_silently=False,  # This will raise an exception if the email fails to send
            )

        # Print the number of agents notified
        print(f'{len(agents)} agent(s) notified of upcoming license expirations.')
        # Print the email addresses of the agents that were notified
        print(f'Agents notified:\n {"\n".join([Agent.objects.get(id=agent['agent']).user.email for agent in agents])}\n')
