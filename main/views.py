from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.template.loader import render_to_string
from django.db.models import Q
from .models import Hospital, Doctor, Appointment

# HTMX Views
def doctor_search(request):
    query = request.GET.get('q', '')
    specialization = request.GET.get('specialization', '')
    hospital_id = request.GET.get('hospital', '')
    
    doctors = Doctor.objects.filter(is_active=True)
    
    if query:
        doctors = doctors.filter(
            Q(name__icontains=query) | 
            Q(specialization__icontains=query) |
            Q(bio__icontains=query)
        )
    
    if specialization:
        doctors = doctors.filter(specialization=specialization)
    
    if hospital_id:
        doctors = doctors.filter(hospital_id=hospital_id)
    
    # HTMX запрос
    if request.headers.get('HX-Request'):
        return render(request, 'main/partials/doctor_list_results.html', {
            'doctors': doctors,
            'request': request
        })
    
    return render(request, 'main/doctor_list.html', {
        'doctors': doctors
    })

def load_available_times(request, doctor_id):
    """Загрузка доступных времен для записи"""
    date = request.GET.get('date')
    doctor = get_object_or_404(Doctor, id=doctor_id)
    
    # Логика получения доступных времен
    
    times = ['09:00', '10:00', '11:00', '14:00', '15:00']#Пример
    
    return render(request, 'main/partials/time_slots.html', {
        'times': times,
        'doctor': doctor
    })

def create_appointment_htmx(request, doctor_id):
    """Создание записи через HTMX"""
    if request.method == 'POST':
        doctor = get_object_or_404(Doctor, id=doctor_id)
        
        # Обработка формы
        appointment_date = request.POST.get('appointment_date')
        appointment_time = request.POST.get('appointment_time')
        reason = request.POST.get('reason', '')
        
        try:
            # Создание записи
            appointment = Appointment.objects.create(
                patient=request.user.patient,
                doctor=doctor,
                appointment_date=appointment_date,
                appointment_time=appointment_time,
                reason=reason,
                status='pending'
            )
            
            return render(request, 'main/partials/appointment_success.html', {
                'appointment': appointment
            })
            
        except Exception as e:
            return render(request, 'main/partials/appointment_error.html', {
                'error': str(e)
            })
    
    return render(request, 'main/partials/appointment_form.html', {
        'doctor_id': doctor_id
    })