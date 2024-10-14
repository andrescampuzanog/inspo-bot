from django.urls import path

from . import views

urlpatterns = [
    path("", views.upload, name="upload"),
    path("resources/", views.resources, name="resources"),
    path("search/", views.search, name="search"),
]