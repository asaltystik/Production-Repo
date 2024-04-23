from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


# Form for the login page
class LoginForm(forms.Form):
    username = forms.CharField(label='Username', max_length=100)
    password = forms.CharField(label='Password', widget=forms.PasswordInput)


# Form for the user registration page
class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(label='Email')

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2')
