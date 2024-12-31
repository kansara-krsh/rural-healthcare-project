from django.urls import path
from . import views

app_name = 'patients'

urlpatterns = [
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('signup/', views.signup_view, name='signup'),
    path('logout/', views.logout_view, name='logout'),
    path('make-appointment/', views.make_appointment, name='make_appointment'),
    path('patients/', views.patient_list, name='patient_list'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('patient/<int:patient_id>/', views.patient_detail, name='patient_detail'),
    path('patient/<int:patient_id>/edit/', views.patient_edit, name='patient_edit'),
    path('add-patient/', views.add_patient, name='add_patient'),
    path('medicines/', views.medicines_view, name='medicines'),
    path('report/', views.report_view, name='report'),
    path('contact/', views.contact_view, name='contact'),
]
