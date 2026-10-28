from django.urls import path

from src.server.views import index

urlpatterns = [
    path("/", index, name="test"),
]
