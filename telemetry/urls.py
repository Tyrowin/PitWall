# telemetry/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # URL for the form page (root of the app)
    path("", views.select_session, name="select_session"),  # THIS LINE IS CRUCIAL
    # URL for displaying the data, using parameters from the URL
    path(
        "session/<int:year>/<str:gp>/<str:session_type>/",
        views.display_session_data,
        name="display_data",
    ),
]
