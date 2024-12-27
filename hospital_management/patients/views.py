from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from .models import Patient, Appointment

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('patients:home')
        else:
            # Add error message handling here if needed
            return render(request, 'patients/login.html')
    return render(request, 'patients/login.html')

@login_required
def home(request):
    return render(request, 'patients/base.html')

@login_required
def patient_list(request):
    patients = Patient.objects.all()
    return render(request, 'patients/patient_list.html', {'patients': patients})

@login_required
def appointment_list(request):
    appointments = Appointment.objects.all()
    return render(request, 'patients/appointment_list.html', {'appointments': appointments})