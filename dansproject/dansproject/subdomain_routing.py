from django.urls import path

from dansapp import views

urlpatterns = [
    path("", views.norberts_gambit, name="norberts_gambit"),
    path("scrape_spreads/<str:ticker>", views.scrape_spreads, name="scrape_spreads"),
    path("api", views.norberts_gambit_api, name="norberts_gambit_api"),
    path("tax", views.norberts_gambit_tax, name="norberts_gambit_tax"),
    path("<str:crudop>", views.norberts_gambit, name="norberts_gambit"),
    path("<str:crudop>/<str:name>", views.norberts_gambit, name="norberts_gambit"),
]