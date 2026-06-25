from django.urls import path

from lacommunaute.documentation import views


app_name = "documentation"


urlpatterns = [
    path("", views.DocumentationIndexView.as_view(), name="index"),
    path("<str:slug>", views.DocumentationCategoryView.as_view(), name="category"),
    path("card/<str:slug>", views.DocumentationCardView.as_view(), name="card"),
]
