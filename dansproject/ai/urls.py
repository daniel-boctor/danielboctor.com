from django.urls import path

from . import views

urlpatterns = [
    path("tictactoe", views.tictactoe, name="tictactoe"),
    path("tictactoe_api/<str:algorithm>/<int:training>", views.tictactoe_api, name="tictactoe_api"),
    path("nim", views.nim, name="nim"),
    path("nim_api/<str:algorithm>/<int:training>", views.nim_api, name="nim_api"),
    path("neural-nets", views.neural_nets, name="neural-nets"),
    path("neural-nets_api/<int:width>", views.neural_nets_api, name="neural-nets_api")
]