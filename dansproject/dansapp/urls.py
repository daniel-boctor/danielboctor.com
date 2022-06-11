from django.urls import path
from django.contrib.auth import views as auth_views

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    #user routes
    path("login", auth_views.LoginView.as_view(template_name="dansapp/user/login.html"), name="login"),
    path("logout", auth_views.LogoutView.as_view(template_name="dansapp/user/logout.html"), name="logout"),
    path("password-reset", auth_views.PasswordResetView.as_view(template_name="dansapp/user/password_reset.html"), name="password_reset"),
    path("password-reset/done", auth_views.PasswordResetDoneView.as_view(template_name="dansapp/user/password_reset_done.html"), name="password_reset_done"),
    path("password-reset-confirm/<uidb64>/<token>", auth_views.PasswordResetConfirmView.as_view(template_name="dansapp/user/password_reset_confirm.html"), name="password_reset_confirm"),
    path("password-complete", auth_views.PasswordResetCompleteView.as_view(template_name="dansapp/user/password_reset_complete.html"), name="password_reset_complete"),
    path("register", views.register, name="register"),
    path("user/<str:username>", views.user, name="user"),
    path("user/<str:username>/portfolios", views.portfolios, name="portfolios"),
    #misc
    path("about", views.about, name="about"),
    path("portfolio_api/<str:name>", views.portfolio_api, name="portfolio_api"),
    #finance routes
    path("backtest", views.backtest, name="backtest"),
    path("rolling", views.rolling, name="rolling"),
    path("factors", views.factors, name="factors")
]

from django.conf import settings
from django.conf.urls.static import static

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)