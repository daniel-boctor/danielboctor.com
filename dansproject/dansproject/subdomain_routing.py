from django.urls import path

from dansapp import views

urlpatterns = [
    path("", views.norberts_gambit, name="norberts_gambit")
]