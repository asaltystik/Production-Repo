from django.core.management.base import BaseCommand
import os


# This function will loop through line by line to get the Product name and relevant companies
# Honestly, Might be better to Deprecate this function, Dont know if it is still
# Useful to the project
class Command(BaseCommand):

    help = "Grabs the ancillary products and companies from a txt file and saves it to a json"

    # Argument to get the file path
    def add_arguments(self, parser):
        parser.add_argument('file_path', nargs='?', type=str, help='Must be a txt file')
        return 0

    # Handle function to parse the txt file
    def handle(self, *args, **options):
        file = options['file_path']
        # Open the pdf
        with open(file) as file:
            product_list = {}
            current_product = ""
            # loop through the lines
            for line in file:
                line = line.strip()
                # if the line is all caps it is a product name
                if line.isupper():
                    current_product = line
                    product_list[current_product] = []
                elif current_product is not None:
                    product_list[current_product].append(line)
            print(product_list)
            product_list = str(product_list).replace("'", "\"")
            # Save the product list to a file in static dir
            with open(os.path.join(os.getcwd(), 'static', 'NetworkInsuranceCarriers.json'), "w") as output:
                output.write(str(product_list))
                print("File Saved")
        return 0
