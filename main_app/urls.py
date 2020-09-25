"""student_management_system URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views, hod_views
urlpatterns = [
    path("", views.login_page),
    path("doLogin/", views.doLogin),
    path("get_user_details/", views.getUserDetails),
    path("logout_user/", views.logout_user),
    path("admin_home/", hod_views.admin_home),
    path("add_staff/", hod_views.add_staff),
    path("add_course/", hod_views.add_course),
    path("add_student/", hod_views.add_student),
    path("add_subject/", hod_views.add_subject),
    path("manage_staff/", hod_views.manage_staff),
]
