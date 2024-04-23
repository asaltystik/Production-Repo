from django.views.decorators.clickjacking import xframe_options_exempt
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.core.exceptions import SuspiciousOperation
from django.shortcuts import get_object_or_404
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import FileResponse
from .forms import LoginForm, UserRegistrationForm
from .models import Form, LicensedState
from datetime import timedelta
import os


# This function will render the register.html page
def register_view(request):

    # if the request is a POST request, check if the form is valid
    if request.method == 'POST':

        # create a new user registration form with the POST data
        form = UserRegistrationForm(request.POST)

        # if the form is valid, save the form and redirect the user to the login page
        if form.is_valid():
            form.save()
            return redirect('Login')
    # if the request is not a POST request, create a new user registration form
    else:
        form = UserRegistrationForm()
    return render(request, 'register.html', {'form': form})  # render the register.html page with the form


# this function will render the login.html page
def login_view(request):

    # If the user is already logged in, redirect them to the agent map page
    if request.user.is_authenticated:
        return redirect('AgentMap')

    # if the request is a POST request, check if the form is valid
    if request.method == 'POST':
        # create a new login form with the POST data
        form = LoginForm(request.POST)
        # if the form is valid, authenticate the user and log them in
        if form.is_valid():
            # authenticate the user
            user = authenticate(request, username=form.cleaned_data['username'], password=form.cleaned_data['password'])
            # if the user is not None, log them in
            if user is not None:
                login(request, user)
                return redirect('AgentMap')  # redirect the user to the agent map page
    else:
        # if the request is not a POST request, create a new login form
        form = LoginForm()
    # render the login.html page with the form
    return render(request, 'login.html', {'form': form})


# This function will log the user out and redirect them to the login page
def logout_view(request):
    logout(request)  # log the user out
    return redirect('Login')  # redirect the user to the login page


# This function will render the map.html page
@login_required
def agent_map(request):

    # Get all the states that the agent is licensed in
    licensed_states = LicensedState.objects.filter(agent__user=request.user)
    return render(request, 'map.html', {'licensed_states': licensed_states})


@login_required
# This function will get all the companies in the given state
def get_companies(request, state_code):

    # Dictionary to hold the eapp_url for each company, Key is the company name as it appears in the database
    app_urls = {
        "AARP": "Google.com",
        "AARP United HealthCare Insurance": "google.com",
        "Ace Chubb": "service.iasadmin.com/gateway/login.aspx?pp=pFHD&pn=NR&y1tv0=n",
        "Aetna": "google.com",
        "Aflac": "www.suppinsadmin.com/ssitpa/afl/login.fcc?TYPE=33554433&REALMOID=06-7c8fa642-baed-4867-8961-14bbfb4570e0&GUID=&SMAUTHREASON=0&METHOD=GET&SMAGENTNAME=-SM-s%2f6v5SUbVzQ4z7UXJxBz1wUImgrt7d09vvkdd9fkkP9Ia%2bY2%2bQKSP728d%2fTN%2bXjQ&TARGET=-SM-HTTPS%3a%2f%2fwww%2esuppinsadmin%2ecom%2fssitpa%2ftpaSecure%2fafl%2faflHome%2ehtml",
        "American Benefit Life": "www.suppinsadmin.com/ssitpa/abl/login.fcc?TYPE=167772161&REALMOID=06-4066f660-248b-4614-bd5e-fb7f8d94f6d2&GUID=0&SMAUTHREASON=0&METHOD=GET&SMAGENTNAME=-SM-s%2f6v5SUbVzQ4z7UXJxBz1wUImgrt7d09vvkdd9fkkP9Ia%2bY2%2bQKSP728d%2fTN%2bXjQ&TARGET=-SM-HTTPS%3a%2f%2fwww%2esuppinsadmin%2ecom%2fssitpa%2ftpaSecure%2fabl%2fablHome%2ehtml",
        "American Financial Security": "www.suppinsadmin.com/ssitpa/afs/login.fcc?TYPE=33554433&REALMOID=06-ce8b1672-46e5-41bd-85e9-85413567cd16&GUID=&SMAUTHREASON=0&METHOD=GET&SMAGENTNAME=-SM-s%2f6v5SUbVzQ4z7UXJxBz1wUImgrt7d09vvkdd9fkkP9Ia%2bY2%2bQKSP728d%2fTN%2bXjQ&TARGET=-SM-HTTPS%3a%2f%2fwww%2esuppinsadmin%2ecom%2fssitpa%2ftpaSecure%2fafs%2fafsHome%2ehtml",
        "American Home Life": "www.suppinsadmin.com/ssitpa/amh/login.fcc?TYPE=33554433&REALMOID=06-f9efb62f-7746-4632-a0d8-8046577e1448&GUID=&SMAUTHREASON=0&METHOD=GET&SMAGENTNAME=-SM-s%2f6v5SUbVzQ4z7UXJxBz1wUImgrt7d09vvkdd9fkkP9Ia%2bY2%2bQKSP728d%2fTN%2bXjQ&TARGET=-SM-HTTPS%3a%2f%2fwww%2esuppinsadmin%2ecom%2fssitpa%2ftpaSecure%2famh%2famhHome%2ehtml",
        "Bankers Fidelity Atlantic American": "agent.bflic.com/Login/Login?usrtyp=A",
        "Cigna Health and Life Insurance": "agentviewcigna.com/AgentView/",
        "Cigna National Health Insurance": "agentviewcigna.com/AgentView/",
        "Cigna Loyal American Life Insurance": "agentviewcigna.com/AgentView/",
        "Elips Life Insurance": "google.com",
        "LifeShield National Insurance": "lsneapp.com/forms/medicare",
        "Lumico": "lumicoagentcenter.com/core/login",
        "Manhattan Life": "producer.manhattanlife.com/life/account/login.aspx",
        "Medico": "mic.gomedico.com/login.aspx",
        "Mutual of Omaha": "www3.mutualofomaha.com/OktaSpaRegistration/home?_ga=2.58007530.1352809056.1683039431-1489991625.1683039431",
        "New Era": "apps.neweralife.com/agentportal/account/login",
        "Philadelphia American Life Insurance": "my.aimc.net/",
        "WPS Health Insurance": "my.wpshealth.com/en/AgentInd"
    }

    # Dictionary to convert state abbreviations to full state names
    state_dictionary = {
        "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "AR": "Arkansas",
        "CA": "California", "CO": "Colorado", "CT": "Connecticut",
        "DC": "District of Columbia", "DE": "Delaware", "FL": "Florida",
        "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
        "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
        "LA": "Louisiana", "ME": "Maine", "MD": "Maryland", "MA": "Massachusetts",
        "MI": "Michigan", "MN": "Minnesota", "MS": "Mississippi", "MO": "Missouri",
        "MT": "Montana", "NE": "Nebraska", "NV": "Nevada", "NH": "New Hampshire",
        "NJ": "New Jersey", "NM": "New Mexico", "NY": "New York",
        "NC": "North Carolina", "ND": "North Dakota", "OH": "Ohio",
        "OK": "Oklahoma", "OR": "Oregon", "PA": "Pennsylvania",
        "RI": "Rhode Island", "SC": "South Carolina", "SD": "South Dakota",
        "TN": "Tennessee", "TX": "Texas", "UT": "Utah", "VT": "Vermont",
        "VA": "Virginia", "WA": "Washington", "WV": "West Virginia",
        "WI": "Wisconsin", "WY": "Wyoming",
    }

    # Get all the forms in the given state
    forms = Form.objects.filter(state=state_code).order_by('company')

    # Get the un-abbreviated state name using the state code and the StateDict
    state = state_dictionary[state_code]

    # Get the current date
    current_date = timezone.now().date()

    # Try to get the license number and expiration date for the given state
    try:
        # Get all the licenses for the agent
        licenses = LicensedState.objects.filter(agent__user=request.user)
        # Get the state license for the given state and the farthest
        # expiration date for the given state
        state_license = licenses.filter(state=state_code).order_by('expiration').last()
        if state_license is not None:
            license_number = state_license.licenseNumber
            expiration = state_license.expiration
            # Check if the expiration date is upcoming in the next 31 days
            is_expiring_soon = (expiration - current_date <= timedelta(days=31))\
                if expiration else False
            # Im sure future me won't have to deal with this... Sorry, Not sorry.
            days_until_expiration = (expiration - current_date).days \
                if expiration else 9999  # Set to huge number since NaN is not valid
        else:
            license_number = None  # Set to None if no license is found
            expiration = None  # Set to None if no license is found
            is_expiring_soon = False  # Set to False if no license is found
            days_until_expiration = 9999  # Huge number since NaN is not valid

        # Context
        context = {
            "state": state,  # packing the state name into context
            "forms": forms,  # packing the forms into context
            "license_number": license_number,  # packing the license number into context
            "expiration": expiration,  # packing the expiration date into context
            "is_expiring_soon": is_expiring_soon,  # packing the is_expiring_soon boolean into context
            "days_until_expiration": days_until_expiration,  # packing the days until expiration into context
            "app_urls": app_urls  # packing the app_urls dictionary into context
        }

        # Render the companies.html page with the given state, forms, license number, expiration date,
        # and is_expiring_soon
        return render(request, "companies.html", context)
    # If the agent is not licensed in the given state, render the companies.html page with the given state and forms
    except LicensedState.DoesNotExist:

        # Context
        context = {
            "state": state,  # packing the state name into context
            "forms": forms,  # packing the forms into context
            # Set to NaN
            "days_until_expiration": 9999,  # Setting this to huge number since nan is not supported
            "app_urls": app_urls  # packing the app_urls dictionary into context
        }

        # Render the companies.html page with the given state and forms
        return render(request, "companies.html", context)


# This function handles opening the pdf file server side and sending it to the client
@xframe_options_exempt
@login_required
def view_form(request, form_id):

    # Get the form with the given id
    form = get_object_or_404(Form, id=form_id)

    # Get the file path of the form
    file_path = form.file_path

    # if os is windows, replace the backslashes with forward slashes
    if os.name == 'nt':
        # in the future this will be replaced. Windows is not what this server is going to be running on in production
        file_path = file_path.replace('\\', '/')  # Fuck windows \\ should just be /

    # Get the file_path
    # if filepath doesnt contain static/Companies/
    if not file_path.startswith("static/Companies"):
        # file_path does not start with static/Companies
        index = file_path.index("static/Companies")  # Remove the ../.. from the rel path
        file_path = file_path[index:]
    elif "static/Companies" not in file_path:
        file_path = "static/Companies" + file_path  # Simple append to the beginning of the string
    else:
        file_path = file_path  # File_path should be ok as is

    # if the file path does not start with 'static/', raise a SuspiciousOperation
    if not file_path.startswith('static/'):
        raise SuspiciousOperation('Attempted directory traversal')  # Raise a suspicious operation

    # Open the file and send it to the client
    response = FileResponse(open(file_path, 'rb'), content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{os.path.basename(file_path)}"'
    return response
