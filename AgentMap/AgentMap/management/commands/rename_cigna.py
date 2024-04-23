from django.core.management.base import BaseCommand
import os


# This is a management command that will rename all the files in the
# Companies/Cigna directory that have "CIGNA_" in the filename to "CIGNA-"
class Command(BaseCommand):
    help = ("This command renames all files in the Companies/Cigna directory "
            "that have 'CIGNA_' in the filename to 'CIGNA-'")

    # Handle method that is called when the management command is ran.
    def handle(self, *args, **kwargs):
        # Check if the server is running on Windows or Linux
        if os.name == 'nt':
            # If the server is running on Windows, use the Windows path
            directory = "C:\\Users\\Noricum\\Desktop\\WebApps\\TestingSVG\\static\\Companies\\Cigna"
        else:
            # If the server is running on Linux, use the Linux path
            directory = "static/Companies/Cigna"

        # Loop through all the files in the directory
        for filename in os.listdir(directory):
            # Check if the filename contains "CIGNA_"
            if "CIGNA_" in filename:
                # Replace "CIGNA_" with "CIGNA-"
                new_filename = filename.replace("CIGNA_", "CIGNA-")
                # Get the full path of the old and new files
                old_file_path = os.path.join(directory, filename)
                new_file_path = os.path.join(directory, new_filename)
                # Rename the file
                os.rename(old_file_path, new_file_path)
                # Print a message indicating the file was renamed
                print(f"Renamed {filename} to {new_filename}")
            else:
                # Testing to see if the file is not renamed
                print(f"File {filename} was not renamed")
