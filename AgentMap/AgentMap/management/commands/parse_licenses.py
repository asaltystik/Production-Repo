from django.core.management.base import BaseCommand
from AgentMap.models import LicensedState, Agent
from PyPDF2 import PdfReader
import pandas as pd
import tabula
import os


# This command is used to parse the licenses from the SirCon PDFs
class Command(BaseCommand):
    # Help message
    help = 'Parse the licenses from the SirCon PDFs and add them to the database'

    # Add arguments of the path and the name of the agent
    def add_arguments(self, parser):
        parser.add_argument('path', type=str, help='The path to the folder containing the PDFs')
        # I want a second argument to be able to specify the agent name
        parser.add_argument('agent', type=str, help='The name of the agent')

    # Handle function
    def handle(self, *args, **kwargs):
        process_pdf(kwargs['path'], kwargs['agent'])


# Functions Start here
def get_page_count(file_path):
    """
    This function gets the number of pages in a PDF file.

    Parameters:
    file_path (str): The path to the PDF file.

    Returns:
    page_count (int): The number of pages in the PDF file.
    """

    # Open the PDF file
    with open(file_path, 'rb') as file:
        pdf = PdfReader(file)

        # Get the number of pages
        page_count = len(pdf.pages)
        print("Number of pages in the PDF file: ", page_count)
    return page_count


def get_coordinates():
    """
    This function gets the coordinates of a table in a PDF file from the user.

    Returns:
    y1 (float) x 72: The y1 coordinate of the table.
    x1 (float) x 72: The x1 coordinate of the table.
    y2 (float) x 72: The y2 coordinate of the table.
    x2 (float) x 72: The x2 coordinate of the table.
    """

    # Get the y coordinates of the table
    while True:
        try:
            y1 = float(input("Enter the y1 coordinate: ")) * 72
            x1 = float(input("Enter the x1 coordinate: ")) * 72
            y2 = float(input("Enter the y2 coordinate: ")) * 72
            x2 = float(input("Enter the x2 coordinate: ")) * 72
            break
        except ValueError:
            print("Needs to be an integer or float")
    print("Coordinates in tabula space: y1 = ", y1, ", x1 = ", x1, ", y2 = ", y2, ", x2 = ", x2)
    return y1, x1, y2, x2


# function to parse the tables
def process_dataframe(dataframe):
    """
        This function processes a dataframe by performing several operations such as dropping columns,
        removing null rows, shifting values, and setting default values.

        Parameters:
        dataframe (pd.DataFrame): The dataframe to be processed.

        Returns:
        dataframe (pd.DataFrame): The processed dataframe.
        """

    # iterate over the columns in the dataframe
    for column in dataframe.columns:
        # if the column name starts with 'Unnamed' then rename it to the value in the first row
        if column.startswith('Unnamed'):
            # get the value in the first row
            new_column_name = dataframe[column].iloc[0]
            # if the new column name is null then grab the next row
            if new_column_name == 'NaN':
                # get the value in the second row
                new_column_name = dataframe[column].iloc[1]
            # print(new_column_name)

            # rename the column
            dataframe = dataframe.rename(columns={column: new_column_name})
        # if the column name is just LICENSE then rename it to LICENSE NUMBER
        if column == 'LICENSE':
            dataframe = dataframe.rename(columns={column: 'LICENSE NUMBER'})
        # if the column name is just EXPIRATION then rename it to EXPIRATION DATE
        if column == 'EXPIRATION':
            dataframe = dataframe.rename(columns={column: 'EXPIRATION DATE'})
    dataframe = dataframe.drop(dataframe.index[0])

    # print(dataframe)

    # drop the Licensee column if it exists
    dataframe = dataframe.drop(columns=['LICENSEE'], errors='ignore')

    # Drop LICENSE TYPE column
    dataframe = dataframe.drop(columns=['LICENSE TYPE'])

    # Drop Rows where everything is null
    dataframe = dataframe.dropna(how="all")

    # Remove any decimal points from the 'LICENSE NUMBER' column
    dataframe['LICENSE NUMBER'] = dataframe['LICENSE NUMBER'].astype(str).str.replace('\.\d+', '', regex=True)

    # Shift the 'LICENSE NUMBER' and 'EXPIRATION DATE' columns up by 1 maybe 2 if needed
    dataframe['LICENSE NUMBER'] = dataframe['LICENSE NUMBER'].shift(+1)
    dataframe['EXPIRATION DATE'] = dataframe['EXPIRATION DATE'].shift(+1)
    dataframe.loc[dataframe['STATE'].isna(), 'LICENSE NUMBER'] = dataframe.loc[
        dataframe['STATE'].isna(),  # Get the rows where 'STATE' is null
        'LICENSE NUMBER'  # Get the 'LICENSE NUMBER' column
    ].shift(+1)
    dataframe.loc[dataframe['STATE'].isna(), 'EXPIRATION DATE'] = dataframe.loc[
        dataframe['STATE'].isna(),  # Get the rows where 'STATE' is null
        'EXPIRATION DATE'  # Get the 'EXPIRATION DATE' column
    ].shift(+1)

    # Create a mask for rows where 'STATE' is more than 2 characters long
    mask = dataframe['STATE'].str.len() > 2

    # Use the mask to drop these rows
    dataframe = dataframe.loc[~mask]

    # Drop Rows where everything is null
    dataframe = dataframe.dropna(how="all")
    dataframe = dataframe.dropna(subset=['STATE'])

    # Set the 'EXPIRATION DATE' column to 05/31/2999 if it is null
    dataframe['EXPIRATION DATE'] = dataframe['EXPIRATION DATE'].fillna('05/31/2099')

    # Reset the index
    dataframe = dataframe.reset_index(drop=True)

    return dataframe


def process_pdf(file_path, agent_name):
    """
        This function processes a PDF file and saves the data to a CSV file.

        Parameters:
        file_path (str): The path to the PDF file to parse.

        The function performs the following steps:
        1. Asks the user to input the y-coordinates of a table in the PDF file.
        2. Reads the first page of the PDF file using the tabula.read_pdf() function.
        3. Processes the first page of the PDF using the process_dataframe() function.
        4. Prints the first page of the PDF.
        5. Repeats steps 1-4 for the middle pages (pages 2-4) and the last page of the PDF.
        6. Combines all the dataframes into one and performs several operations on the combined dataframe.
        7. Asks the user if they want to manually edit the dataframe. If the user answers 'yes', it allows the user to
         edit the dataframe.
        8. Saves the dataframe to a CSV file in the 'Licenses' folder. The file name is provided by the user.
        9. Gets the current user as the agent and asks the user if they want to add or delete the list from the model.
        It then iterates over the rows in the dataframe to add or delete the licenses.
        """

    # Get the coordinates of the table
    # x1 = 1 * 72
    # x2 = 5.75 * 72

    pages = get_page_count(file_path)

    # Get the y coordinates of the table
    y1, x1, y2, x2 = get_coordinates()

    # Read the first page of the pdf
    df = tabula.read_pdf(file_path, area=[y1, x1, y2, x2], pages=1)

    # process the first page
    df[0] = process_dataframe(df[0])

    # print the first page
    print(df[0])
    # If there are more then 2 pages then we need to process the middle pages
    if pages > 2:
        # Set the value of middle pages
        middle_pages = "2-" + str(pages)

        # Ask the user for the coordinates of the table on pages 2-4
        print("Enter the coordinates of the table in inches for pages " + middle_pages)

        # Get the coordinates of the table
        y1, x1, y2, x2 = get_coordinates()

        # Read all middle pages
        df_following_pages = tabula.read_pdf(file_path, area=[y1, x1, y2, x2], pages=middle_pages)

        # Process the middle pages one at a time
        for i in range(len(df_following_pages) - 1):
            df_following_pages[i] = process_dataframe(df_following_pages[i])

            # print the following pages
            print("Page ", i + 2, ":")
            print(df_following_pages[i])

    # Ask the user for the coordinates of the table on the last page
    print("Enter the coordinates of the table in inches for the last page")

    # Get the coordinates of the table on the last page
    y1, x1, y2, x2 = get_coordinates()

    last_page = str(pages)

    # Read the last page
    df_last_page = tabula.read_pdf(file_path, area=[y1, x1, y2, x2], pages=last_page)

    # Process the last page
    df_last_page[0] = process_dataframe(df_last_page[0])

    # print the last page
    print("Page 5:")
    print(df_last_page[0])

    # Make sure the dataframes are not series
    df = pd.concat(df)
    df_last_page = pd.concat(df_last_page)

    # Check if df_following_pages exists
    if 'df_following_pages' in locals():
        # make sure the dataframe is not a series
        df_following_pages = pd.concat(df_following_pages)
        # Combine all 3 dataframes
        df = pd.concat([df, df_following_pages, df_last_page], ignore_index=True)
    else:
        # Combine the first and last page
        df = pd.concat([df, df_last_page], ignore_index=True)

    # Drop the License Type column
    if 'LICENSE TYPE' in df.columns:
        df = df.drop(columns=['LICENSE TYPE'])

    # Drop rows that are NULL
    df = df.dropna(subset=['LICENSE NUMBER', 'EXPIRATION DATE'])

    # if we have more than 3 columns at this point then we need to drop all columns after the 3rd
    if len(df.columns) > 3:
        df = df.iloc[:, :3]

    # if there is a duplicate STATE then drop the second one
    df = df.drop_duplicates(subset=['STATE'])

    # Reset the index
    df = df.reset_index(drop=True)

    # Format the Expiration Date Column from mm/dd/yyyy to yyyy-mm-dd
    df['EXPIRATION DATE'] = pd.to_datetime(df['EXPIRATION DATE'])

    pd.set_option('display.max_rows', None)  # Display all fucking rows you goober
    # print the final dataframe
    print(df)

    # Ask the user if they want to manually edit the dataframe
    edit = input("Do you want to manually edit the dataframe? (yes/no): ")

    # Loop until we get a valid response
    while edit.lower() == 'yes':
        # Ask the user for the row number to edit
        while True:
            try:
                row_number = int(input("Enter the row number to edit: "))
                break
            except ValueError:
                print("Invalid row number. Please enter an integer.")

        # Ask the user for the column to edit
        while True:
            try:
                column = input("Enter the column to edit(STATE, LICENSE NUMBER, or EXPIRATION DATE): ").upper()
                if column not in ['STATE', 'LICENSE NUMBER', 'EXPIRATION DATE']:
                    raise ValueError
                break
            except ValueError:
                print("Invalid column. Please enter STATE, LICENSE NUMBER, or EXPIRATION DATE.")

        # Ask the user for the new value
        new_value = input("Enter the new value: ")

        # Update the dataframe
        df.at[row_number, column] = new_value

        # Print the updated row
        print(df.loc[row_number])

        # Ask the user if they want to edit another row
        edit = input("Do you want to edit another row? (yes/no): ")

    # Save the dataframe to a csv file in Licenses folder, Ask user for the file name
    df.to_csv("static/Licenses/" + agent_name + ".csv", index=False)

    # Get the current user as the agent
    agent = Agent.objects.get(user__username=agent_name)

    # Ask the user if they want to add or delete the list
    # action = input("Do you want to add or delete this list from the model? (add/delete): ")

    # Iterate over the rows in the dataframe to add or delete the licenses
    for index, row in df.iterrows():
        print(row['STATE'], row['LICENSE NUMBER'], row['EXPIRATION DATE'])
        existing_license = LicensedState.objects.filter(
            agent=agent,  # agent is the current user
            state=row['STATE'],  # state is the state in the row
            licenseNumber=row['LICENSE NUMBER']  # license number is the license number in the row
        ).first()  # Get the first object that matches the query

        if existing_license is None:
            # Create a LicensedState object
            LicensedState.objects.create(
                agent=agent,  # agent is the current user
                state=row['STATE'],  # state is the state in the row
                licenseNumber=row['LICENSE NUMBER'],  # license number is the license number in the row
                expiration=pd.to_datetime(row['EXPIRATION DATE'])  # expiration date is the expiration date in the row
            )
