from django.urls import path
from . import views

urlpatterns = [
    # Основные страницы
    path('', views.dashboard, name='dashboard'),
    path('hospitals/', views.hospital_list, name='hospital_list'),
    path('hospitals/<slug:slug>/', views.hospital_detail, name='hospital_detail'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('doctors/<int:pk>/', views.doctor_detail, name='doctor_detail'),
    
    # HTMX endpoints
    path('doctors/search/', views.doctor_search, name='doctor_search'),
    path('doctors/filter/', views.doctor_filter, name='doctor_filter'),
    path('appointment/<int:doctor_id>/', views.create_appointment_htmx, name='create_appointment'),
    path('appointment/times/<int:doctor_id>/', views.load_available_times, name='get_available_times'),
    path('hospital/search/', views.hospital_search, name='hospital_search'),
]