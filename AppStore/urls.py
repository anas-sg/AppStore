"""AppStore URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
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
from django.contrib import admin
from django.urls import path

import app.views

urlpatterns = [
    # path('admin/', admin.site.urls),
    path('', app.views.index, name='index'),
    path('index', app.views.index, name='index'),
    path('register', app.views.add_user, name='register'),
    path('add_tutor/<int:filled>', app.views.add_tutor, name='add_tutor'),
    path('add_user', app.views.add_user, name='add_user'),
    path('view/<str:student_id_mod_code>', app.views.view, name='view'),
    path('edit/<str:student_id_mod_code>', app.views.edit, name='edit'),
    path('login', app.views.login, name='login'),
    path('logout', app.views.logout, name='logout'),
    path('profile/<str:student_id>', app.views.profile, name='profile'),
    path('users', app.views.users, name='users'),
    path('edit_user/<str:student_id>', app.views.edit_user, name='edit_user'),
    path('modules', app.views.modules, name='modules'),
    path('test', app.views.test, name='test')
]
