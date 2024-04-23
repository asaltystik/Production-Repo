from django.urls import path
from . import views


# URL patterns for the AgentMap web application
urlpatterns = [
    path('login/', views.login_view, name='Login'),  # URL Pattern for the login page
    path('logout/', views.logout_view, name='Logout'),  # URL Pattern for the logout page
    path('register/', views.register_view, name='Register'),  # URL Pattern for the register page
    path('', views.agent_map, name='AgentMap'),  # URL Pattern for the agent map page
]
