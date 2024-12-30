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
from django.http import JsonResponse
from django.conf import settings

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
    
    # Improved search query
    if search_query:
        patients = Patient.objects.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(phone_number__icontains=search_query) |
            Q(email__icontains=search_query)
        ).order_by('-created_at')
    else:
        patients = Patient.objects.all().order_by('-created_at')
    
    # Get patients with alerts
    patients_with_alerts = patients.filter(
        Q(status='pending') |
        Q(updated_at__lt=timezone.now() - timedelta(days=180))
    )
    
    patient_alerts = {
        'total': patients_with_alerts.count(),
        'details': [
            {
                'id': patient.id,
                'name': f"{patient.first_name} {patient.last_name}",
                'reason': 'Pending Review' if patient.status == 'pending' else 'Follow-up Required',
                'days': (timezone.now().date() - patient.updated_at.date()).days,
                'status': patient.status
            }
            for patient in patients_with_alerts[:5]
        ]
    }
    
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
        # Get form data with proper validation
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        date_of_birth = request.POST.get('date_of_birth')
        gender = request.POST.get('gender')
        phone_number = request.POST.get('phone_number')
        email = request.POST.get('email')
        
        # Validate required fields
        if not all([first_name, last_name, date_of_birth, gender, phone_number]):
            messages.error(request, 'Please fill in all required fields')
            return redirect('patients:patient_edit', patient_id=patient_id)
        
        try:
            # Update patient information
            patient.first_name = first_name
            patient.last_name = last_name
            patient.date_of_birth = date_of_birth
            patient.gender = gender
            patient.phone_number = phone_number
            patient.email = email
            patient.save()
            
            messages.success(request, 'Patient information updated successfully')
            return redirect('patients:patient_detail', patient_id=patient_id)
            
        except Exception as e:
            messages.error(request, f'Error updating patient: {str(e)}')
            return redirect('patients:patient_edit', patient_id=patient_id)
    
    context = {
        'patient': patient,
        'page_title': f'Edit Patient: {patient.first_name} {patient.last_name}'
    }
    return render(request, 'patients/patient_edit.html', context)

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
                status='active'
            )
            
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': True,
                    'patient_id': patient.id,
                    'message': 'Patient added successfully!'
                })
            
            messages.success(request, 'Patient added successfully!')
            return redirect('patients:patient_detail', patient_id=patient.id)
            
        except Exception as e:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({
                    'success': False,
                    'error': str(e)
                })
            
            messages.error(request, f'Error adding patient: {str(e)}')
            return redirect('patients:add_patient')
    
    return render(request, 'patients/add_patient.html')

@login_required
def medicines_view(request):
    # Medicine data dictionary
    medicines = {
        'paracetamol': {
            'name': 'Paracetamol',
            'image': 'https://www.drugs.com/images/pills/nlm/004068801.jpg',
            'volume': '500mg',
            'price': '$5.99',
        },
        'amoxicillin': {
            'name': 'Amoxicillin',
            'image': 'https://www.drugs.com/images/pills/nlm/167140513.jpg',
            'volume': '250mg',
            'price': '$8.99',
        },
        # Add all other medicines here...
    }
    
    return render(request, 'patients/medicines.html', {'medicines': medicines})