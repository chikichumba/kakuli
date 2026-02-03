# admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from django.urls import reverse
from django.db.models import Count, Avg
from .models import Hospital, Patient, Doctor, Schedule, Appointment, MedicalRecord


# Inline классы для отображения связанных моделей
class DoctorInline(admin.TabularInline):
    model = Doctor
    extra = 0
    fields = ['name', 'specialization', 'is_active']
    readonly_fields = ['name', 'specialization']


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 0
    fields = ['day_of_week', 'start_time', 'end_time', 'cabinet', 'is_working']
    readonly_fields = ['day_of_week', 'start_time', 'end_time']


class AppointmentInline(admin.TabularInline):
    model = Appointment
    extra = 0
    fields = ['patient', 'appointment_date', 'appointment_time', 'status']
    readonly_fields = ['patient', 'appointment_date', 'appointment_time']


class MedicalRecordInline(admin.TabularInline):
    model = MedicalRecord
    extra = 0
    fields = ['record_date', 'diagnosis', 'type_of_treatment']
    readonly_fields = ['record_date', 'diagnosis']


# Кастомные классы админки
@admin.register(Hospital)
class HospitalAdmin(admin.ModelAdmin):
    list_display = ('name', 'address', 'phone', 'doctors_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'updated_at')
    search_fields = ('name', 'address', 'email', 'phone')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at', 'doctors_count_display', 'photo_preview')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'slug', 'photo', 'photo_preview', 'is_active')
        }),
        (_('Контактная информация'), {
            'fields': ('address', 'email', 'phone')
        }),
        (_('Расписание работы'), {
            'fields': ('start_time', 'end_time')
        }),
        (_('Описание'), {
            'fields': ('description',)
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [DoctorInline]
    actions = ['activate_hospitals', 'deactivate_hospitals']
    
    def doctors_count(self, obj):
        return obj.doctors.count()
    doctors_count.short_description = _('Количество врачей')
    
    def doctors_count_display(self, obj):
        return obj.doctors_count
    doctors_count_display.short_description = _('Врачей в больнице')
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" height="auto" />', obj.photo.url)
        return _("Нет фото")
    photo_preview.short_description = _('Предпросмотр фото')
    
    def activate_hospitals(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('Активировано {} больниц').format(updated))
    activate_hospitals.short_description = _('Активировать выбранные больницы')
    
    def deactivate_hospitals(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('Деактивировано {} больниц').format(updated))
    deactivate_hospitals.short_description = _('Деактивировать выбранные больницы')


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ('name', 'specialization', 'hospital_link', 'experience_years', 
                    'rating', 'is_active', 'appointments_count')
    list_filter = ('is_active', 'specialization', 'hospital', 'created_at')
    search_fields = ('name', 'specialization', 'email', 'phone', 'bio')
    readonly_fields = ('created_at', 'updated_at', 'photo_preview', 
                      'total_appointments', 'average_rating')
    autocomplete_fields = ['hospital']
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('name', 'specialization', 'hospital', 'is_active')
        }),
        (_('Контактная информация'), {
            'fields': ('email', 'phone')
        }),
        (_('Фотография'), {
            'fields': ('photo', 'photo_preview')
        }),
        (_('Профессиональная информация'), {
            'fields': ('bio', 'experience_years', 'rating')
        }),
        (_('Статистика'), {
            'fields': ('total_appointments', 'average_rating')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [ScheduleInline, AppointmentInline]
    actions = ['activate_doctors', 'deactivate_doctors']
    
    def hospital_link(self, obj):
        url = reverse('admin:main_hospital_change', args=[obj.hospital.id])
        return format_html('<a href="{}">{}</a>', url, obj.hospital.name)
    hospital_link.short_description = _('Больница')
    hospital_link.admin_order_field = 'hospital__name'
    
    def appointments_count(self, obj):
        return obj.appointments.count()
    appointments_count.short_description = _('Записей')
    
    def total_appointments(self, obj):
        return obj.appointments.count()
    total_appointments.short_description = _('Всего записей')
    
    def average_rating(self, obj):
        avg = obj.appointments.aggregate(avg_rating=Avg('rating'))['avg_rating']
        return f"{avg:.1f}" if avg else "Нет оценок"
    average_rating.short_description = _('Средняя оценка пациентов')
    
    def photo_preview(self, obj):
        if obj.photo:
            return format_html('<img src="{}" width="150" height="auto" />', obj.photo.url)
        return _("Нет фото")
    photo_preview.short_description = _('Предпросмотр фото')
    
    def activate_doctors(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('Активировано {} врачей').format(updated))
    activate_doctors.short_description = _('Активировать выбранных врачей')
    
    def deactivate_doctors(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('Деактивировано {} врачей').format(updated))
    deactivate_doctors.short_description = _('Деактивировать выбранных врачей')
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            appointment_count=Count('appointments')
        ).order_by('-appointment_count')


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'email', 'phone', 'age', 'gender', 
                    'appointments_count', 'is_active', 'created_at')
    list_filter = ('is_active', 'gender', 'created_at')
    search_fields = ('first_name', 'last_name', 'middle_name', 'email', 'phone')
    readonly_fields = ('created_at', 'updated_at', 'age_display', 'slug', 
                      'total_appointments', 'upcoming_appointments')
    prepopulated_fields = {'slug': ('last_name', 'first_name')}
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('first_name', 'last_name', 'middle_name', 'slug', 'is_active')
        }),
        (_('Контактная информация'), {
            'fields': ('email', 'phone', 'address')
        }),
        (_('Личная информация'), {
            'fields': ('date_of_birth', 'gender', 'age_display', 
                      'blood_type', 'allergies')
        }),
        (_('Медицинская информация'), {
            'fields': ('emergency_contact', 'insurance_number')
        }),
        (_('Статистика'), {
            'fields': ('total_appointments', 'upcoming_appointments')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    inlines = [AppointmentInline, MedicalRecordInline]
    actions = ['activate_patients', 'deactivate_patients']
    
    def full_name(self, obj):
        return obj.full_name
    full_name.short_description = _('ФИО')
    full_name.admin_order_field = 'last_name'
    
    def appointments_count(self, obj):
        return obj.appointments.count()
    appointments_count.short_description = _('Записей')
    
    def age_display(self, obj):
        return f"{obj.age} лет"
    age_display.short_description = _('Возраст')
    
    def total_appointments(self, obj):
        return obj.appointments.count()
    total_appointments.short_description = _('Всего записей')
    
    def upcoming_appointments(self, obj):
        from django.utils import timezone
        return obj.appointments.filter(
            appointment_date__gte=timezone.now().date(),
            status='confirmed'
        ).count()
    upcoming_appointments.short_description = _('Предстоящие записи')
    
    def activate_patients(self, request, queryset):
        updated = queryset.update(is_active=True)
        self.message_user(request, _('Активировано {} пациентов').format(updated))
    activate_patients.short_description = _('Активировать выбранных пациентов')
    
    def deactivate_patients(self, request, queryset):
        updated = queryset.update(is_active=False)
        self.message_user(request, _('Деактивировано {} пациентов').format(updated))
    deactivate_patients.short_description = _('Деактивировать выбранных пациентов')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week_display', 'start_time', 'end_time', 
                    'cabinet', 'is_working', 'appointment_duration')
    list_filter = ('day_of_week', 'is_working', 'reception_type', 'doctor__hospital')
    search_fields = ('doctor__name', 'cabinet')
    readonly_fields = ('created_at', 'updated_at', 'total_slots', 'available_slots')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('doctor', 'cabinet', 'is_working', 'reception_type')
        }),
        (_('Расписание'), {
            'fields': ('day_of_week', 'start_time', 'end_time', 'appointment_duration')
        }),
        (_('Расчеты'), {
            'fields': ('total_slots', 'available_slots')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['activate_schedules', 'deactivate_schedules']
    
    def day_of_week_display(self, obj):
        return obj.get_day_of_week_display()
    day_of_week_display.short_description = _('День недели')
    day_of_week_display.admin_order_field = 'day_of_week'
    
    def total_slots(self, obj):
        # Расчет общего количества слотов
        from datetime import datetime, timedelta
        if obj.start_time and obj.end_time:
            start = datetime.combine(datetime.today(), obj.start_time)
            end = datetime.combine(datetime.today(), obj.end_time)
            duration = timedelta(minutes=obj.appointment_duration)
            
            slots = 0
            current = start
            while current + duration <= end:
                slots += 1
                current += duration
            return slots
        return 0
    total_slots.short_description = _('Всего слотов')
    
    def available_slots(self, obj):
        # Расчет доступных слотов (без учета уже занятых)
        from django.utils import timezone
        from datetime import datetime, timedelta
        
        today = timezone.now().date()
        if obj.start_time and obj.end_time:
            # Примерная логика расчета
            total = self.total_slots(obj)
            
            # Занятые слоты (нужно реализовать логику)
            booked = Appointment.objects.filter(
                doctor=obj.doctor,
                appointment_date=today,
                status__in=['pending', 'confirmed']
            ).count()
            
            return max(0, total - booked)
        return 0
    available_slots.short_description = _('Доступных слотов сегодня')
    
    def activate_schedules(self, request, queryset):
        updated = queryset.update(is_working=True)
        self.message_user(request, _('Активировано {} расписаний').format(updated))
    activate_schedules.short_description = _('Активировать выбранные расписания')
    
    def deactivate_schedules(self, request, queryset):
        updated = queryset.update(is_working=False)
        self.message_user(request, _('Деактивировано {} расписаний').format(updated))
    deactivate_schedules.short_description = _('Деактивировать выбранные расписания')


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'appointment_datetime', 'status_display', 
                    'price', 'is_upcoming', 'reminder_sent')
    list_filter = ('status', 'appointment_date', 'created_at', 'reminder_sent')
    search_fields = ('patient__first_name', 'patient__last_name', 
                    'doctor__name', 'reason', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'appointment_datetime_display',
                      'duration_display', 'is_upcoming_display')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('patient', 'doctor', 'status')
        }),
        (_('Время приема'), {
            'fields': ('appointment_date', 'appointment_time', 
                      'appointment_datetime_display', 'duration_display')
        }),
        (_('Детали'), {
            'fields': ('reason', 'notes', 'price')
        }),
        (_('Системная информация'), {
            'fields': ('created_by', 'reminder_sent', 'is_upcoming_display')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    actions = ['confirm_appointments', 'cancel_appointments', 'mark_as_completed',
               'send_reminders', 'mark_reminder_sent']
    
    def status_display(self, obj):
        colors = {
            'pending': 'warning',
            'confirmed': 'success',
            'cancelled': 'danger',
            'completed': 'info',
            'no_show': 'secondary'
        }
        color = colors.get(obj.status, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_status_display()
        )
    status_display.short_description = _('Статус')
    
    def appointment_datetime(self, obj):
        return f"{obj.appointment_date} {obj.appointment_time}"
    appointment_datetime.short_description = _('Дата и время')
    appointment_datetime.admin_order_field = 'appointment_date'
    
    def appointment_datetime_display(self, obj):
        return f"{obj.appointment_date.strftime('%d.%m.%Y')} {obj.appointment_time.strftime('%H:%M')}"
    appointment_datetime_display.short_description = _('Дата и время приема')
    
    def duration_display(self, obj):
        return f"{obj.duration} минут"
    duration_display.short_description = _('Длительность приема')
    
    def is_upcoming_display(self, obj):
        if obj.is_upcoming:
            return format_html('<span class="badge bg-success">Да</span>')
        return format_html('<span class="badge bg-secondary">Нет</span>')
    is_upcoming_display.short_description = _('Предстоящий прием')
    
    def confirm_appointments(self, request, queryset):
        updated = queryset.update(status='confirmed')
        self.message_user(request, _('Подтверждено {} записей').format(updated))
    confirm_appointments.short_description = _('Подтвердить выбранные записи')
    
    def cancel_appointments(self, request, queryset):
        updated = queryset.update(status='cancelled')
        self.message_user(request, _('Отменено {} записей').format(updated))
    cancel_appointments.short_description = _('Отменить выбранные записи')
    
    def mark_as_completed(self, request, queryset):
        updated = queryset.update(status='completed')
        self.message_user(request, _('Отмечено как завершено {} записей').format(updated))
    mark_as_completed.short_description = _('Отметить как завершенные')
    
    def send_reminders(self, request, queryset):
        # Логика отправки напоминаний
        count = 0
        for appointment in queryset.filter(reminder_sent=False, is_upcoming=True):
            try:
                appointment.send_reminder()
                count += 1
            except Exception as e:
                self.message_user(request, _('Ошибка отправки: {}').format(str(e)), level='error')
        self.message_user(request, _('Отправлено {} напоминаний').format(count))
    send_reminders.short_description = _('Отправить напоминания')
    
    def mark_reminder_sent(self, request, queryset):
        updated = queryset.update(reminder_sent=True)
        self.message_user(request, _('Отмечено {} напоминаний как отправленные').format(updated))
    mark_reminder_sent.short_description = _('Отметить напоминания как отправленные')


@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'record_date', 'diagnosis_short', 
                    'type_of_treatment_display', 'cost')
    list_filter = ('record_date', 'type_of_treatment', 'doctor')
    search_fields = ('patient__first_name', 'patient__last_name', 
                    'diagnosis', 'symptoms', 'treatment')
    readonly_fields = ('record_date', 'created_at', 'updated_at')
    fieldsets = (
        (_('Основная информация'), {
            'fields': ('patient', 'doctor', 'appointment', 'record_date')
        }),
        (_('Медицинская информация'), {
            'fields': ('symptoms', 'diagnosis', 'treatment')
        }),
        (_('Финансовая информация'), {
            'fields': ('cost', 'type_of_treatment')
        }),
        (_('Метаданные'), {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def diagnosis_short(self, obj):
        if len(obj.diagnosis) > 50:
            return f"{obj.diagnosis[:50]}..."
        return obj.diagnosis
    diagnosis_short.short_description = _('Диагноз')
    
    def type_of_treatment_display(self, obj):
        colors = {
            'outpatient': 'info',
            'inpatient': 'warning'
        }
        color = colors.get(obj.type_of_treatment, 'secondary')
        return format_html(
            '<span class="badge bg-{}">{}</span>',
            color, obj.get_type_of_treatment_display()
        )
    type_of_treatment_display.short_description = _('Тип лечения')


# Кастомная админ-панель
admin.site.site_header = _('Панель управления системой записи в больницу')
admin.site.site_title = _('Администрирование больницы')
admin.site.index_title = _('Управление данными')