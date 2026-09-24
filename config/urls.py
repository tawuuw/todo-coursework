from django.contrib import admin
from django.contrib.auth import views as auth_views
from django.urls import include, path
from tasks.views import register

admin.site.site_header = "ToDo — управление приложением"
admin.site.site_title = "Администрирование ToDo"
admin.site.index_title = "Разделы и задачи"

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/register/", register, name="register"),
    path("accounts/login/", auth_views.LoginView.as_view(
        template_name="registration/login.html", redirect_authenticated_user=True
    ), name="login"),
    path("accounts/logout/", auth_views.LogoutView.as_view(), name="logout"),
    path("", include("tasks.urls")),
]

