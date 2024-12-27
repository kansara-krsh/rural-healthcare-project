from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.models import User
from .models import Patient, Appointment
from django.utils import timezone
from datetime import datetime, timedelta
from django.db.models import Q

def login_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('patients:dashboard')
        else:
            messages.error(request, 'Invalid username or password')
            return render(request, 'patients/login.html')
    return render(request, 'patients/login.html')

@login_required
def home(request):
    return render(request, 'patients/index.html')

@login_required
def patient_list(request):
    search_query = request.GET.get('search', '')
    
    # Get total patients count
    total_patients = Patient.objects.count()
    
    # Get patients with alerts (example criteria)
    # 1. Patients with pending status
    # 2. Patients who haven't visited in last 6 months
    # 3. Patients with critical conditions
    six_months_ago = datetime.now() - timedelta(days=180)
    
    patients_with_alerts = Patient.objects.filter(
        Q(status='pending') |
        Q(updated_at__lt=six_months_ago)
    )
    
    patient_alerts = {
        'total': patients_with_alerts.count(),
        'details': [
            {
                'id': patient.id,
                'name': f"{patient.first_name} {patient.last_name}",
                'reason': 'Pending Review' if patient.status == 'pending' else 'Follow-up Required',
                'days': (datetime.now().date() - patient.updated_at.date()).days,
                'status': patient.status
            }
            for patient in patients_with_alerts[:5]  # Get latest 5 alerts
        ]
    }
    
    if search_query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query)
        )
    else:
        patients = Patient.objects.all()
    
    context = {
        'patients': patients,
        'search_query': search_query,
        'total_patients': total_patients,
        'patient_alerts': patient_alerts,
    }
    
    return render(request, 'patients/patient_list.html', context)

@login_required
def appointment_list(request):
    appointments = Appointment.objects.all()
    return render(request, 'patients/appointment_list.html', {'appointments': appointments})

def signup_view(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password1 = request.POST['password1']
        password2 = request.POST['password2']

        if password1 == password2:
            if User.objects.filter(username=username).exists():
                messages.error(request, 'Username already exists')
                return redirect('patients:signup')
            elif User.objects.filter(email=email).exists():
                messages.error(request, 'Email already exists')
                return redirect('patients:signup')
            else:
                user = User.objects.create_user(username=username, email=email, password=password1)
                login(request, user)
                return redirect('patients:home')
        else:
            messages.error(request, 'Passwords do not match')
            return redirect('patients:signup')
    return render(request, 'patients/signup.html')

def logout_view(request):
    logout(request)
    return redirect('patients:home')

def make_appointment(request):
    if not request.user.is_authenticated:
        return redirect('patients:login')
    # Add your appointment logic here
    return render(request, 'patients/make_appointment.html')

@login_required
def dashboard(request):
    # Get statistics
    total_patients = Patient.objects.count()
    today = timezone.now().date()
    
    # Simplified queries without status
    today_appointments = Appointment.objects.filter(appointment_date=today).count()
    pending_appointments = 0  # Temporary until status field is added
    
    # Get recent appointments without status ordering
    recent_appointments = Appointment.objects.all().order_by('-appointment_date', '-created_at')[:5]
    
    context = {
        'total_patients': total_patients,
        'today_appointments': today_appointments,
        'pending_appointments': pending_appointments,
        'recent_appointments': recent_appointments,
    }
    return render(request, 'patients/dashboard.html', context)

@login_required
def patient_detail(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    return render(request, 'patients/patient_detail.html', {
        'patient': patient
    })

@login_required
def patient_edit(request, patient_id):
    patient = get_object_or_404(Patient, id=patient_id)
    
    if request.method == 'POST':
        # Handle form submission
        patient.first_name = request.POST.get('first_name')
        patient.last_name = request.POST.get('last_name')
        patient.date_of_birth = request.POST.get('date_of_birth')
        patient.gender = request.POST.get('gender')
        patient.phone_number = request.POST.get('phone_number')
        patient.email = request.POST.get('email')
        patient.address = request.POST.get('address')
        patient.blood_group = request.POST.get('blood_group')
        patient.medical_history = request.POST.get('medical_history')
        patient.current_medications = request.POST.get('current_medications')
        patient.save()
        
        messages.success(request, 'Patient details updated successfully')
        return redirect('patients:patient_detail', patient_id=patient.id)
    
    return render(request, 'patients/patient_edit.html', {
        'patient': patient
    })

@login_required
def add_patient(request):
    if request.method == 'POST':
        try:
            patient = Patient.objects.create(
                first_name=request.POST.get('first_name'),
                last_name=request.POST.get('last_name'),
                date_of_birth=request.POST.get('date_of_birth'),
                gender=request.POST.get('gender'),
                phone_number=request.POST.get('phone_number'),
                email=request.POST.get('email'),
                address=request.POST.get('address'),
                blood_group=request.POST.get('blood_group'),
                status='active'  # Set default status as active
            )
            messages.success(request, 'Patient added successfully!')
            return redirect('patients:patient_detail', patient_id=patient.id)
        except Exception as e:
            messages.error(request, f'Error adding patient: {str(e)}')
            return redirect('patients:add_patient')
    
    return render(request, 'patients/add_patient.html')