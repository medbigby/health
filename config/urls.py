"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
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
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from healthapp.views import home, register, login_view, logout_view, complete_profile, appointment_view, doctor_appointments_view, get_available_slots
from healthapp import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', TemplateView.as_view(template_name='home.html'), name='home'),
    path('login/', login_view, name='login'),
    path('dashboard/', home, name='dashboard'),
    path('register/', register, name='register'),
    path('logout/', logout_view, name='logout'),
    path('complete-profile/', complete_profile, name='complete_profile'),

    path('search-medicament/', views.recherche_view, name='search_medicament'),
    path('add-medicament/', views.add_medicament, name='add_medicament'),
    path('prescriptions/', views.list_prescriptions, name='list_prescriptions'),
    path('save-prescription/', views.save_and_print_prescription, name='save_prescription'),
    path('prescriptions/<int:pk>/delete/', views.delete_prescription, name='delete_prescription'),
    path('appointment/', appointment_view, name='appointment'),
    path('doctor-appointments/', doctor_appointments_view, name='doctor_appointments'),
    path('api/available-slots/', get_available_slots, name='get_available_slots'),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
