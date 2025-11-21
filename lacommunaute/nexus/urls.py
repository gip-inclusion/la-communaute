from django.urls import path

from lacommunaute.nexus import views


app_name = "nexus"

urlpatterns = [
    path("auto-login", views.auto_login, name="auto_login"),
]
