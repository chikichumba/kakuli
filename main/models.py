from django.db import models
from django.utils.text import slugify
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from datetime import date


import logging
logger = logging.getLogger(__name__)

class Hospital(models.Model):
    is_active = models.BooleanField(default=True, verbose_name=_('Активна'))
    name = models.CharField(max_length=100, unique=True, verbose_name=_("Название"))
    photo = models.ImageField(upload_to='hospitals/', blank=True,null=True,verbose_name=_('Фото'))
    address = models.CharField(max_length=100, verbose_name=_("Адрес"))
    email = models.EmailField(max_length=100, unique=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Телефон"))
    start_time = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        verbose_name=_('Начало работы'),
        )
    end_time = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(24)],
        verbose_name=_('Закрытие'),
        )
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name=_("URL"))
    description = models.TextField(blank=True, verbose_name=_("Описание"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('model-detail', args=[str(self.id)])


    class Meta:
        ordering = ['name']
        verbose_name = _('Больница')
        verbose_name_plural = _('Больницы')
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['created_at']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Hospital.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    @property
    def working_hours_display(self):
        '''Отображение рабочих часов'''
        start_hour = self.start_time
        end_hour = self.end_time
        return f"{start_hour:02d}:00-{end_hour:02d}:00"
    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError(_("Время начала должно быть раньше времени окончания"))
    @property
    def doctors_count(self):
        return self.doctors.count()
    @property
    def is_open_now(self):
        now = timezone.now()
        current_hour = now.hour
        return self.start_time <= current_hour < self.end_time


class Doctor(models.Model):
    name = models.CharField(max_length=100, verbose_name=_("ФИО врача"))
    specialization = models.CharField(max_length=200, verbose_name=_("Специализация"))
    email = models.EmailField(max_length=200, unique=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=20, blank=True, verbose_name=_("Телефон"))
    bio = models.TextField(blank=True, verbose_name=_("Биография"))
    photo = models.ImageField(upload_to='doctors/', blank=True, null=True, verbose_name=_("Фотография"))
    experience_years = models.IntegerField(default=0, verbose_name=_("Стаж (лет)"))
    is_active = models.BooleanField(default=True, verbose_name=_("Активен"))
    hospital = models.ForeignKey(
        Hospital,
        on_delete=models.CASCADE,
        related_name='doctors',
        verbose_name=_('Больница')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))
    rating = models.FloatField(verbose_name=_('Рейтинг врача'), 
                               validators= [MinValueValidator(0), MaxValueValidator(5)],
                               default=0)
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('model-detail', args=[str(self.id)])

    class Meta:
        ordering = ['name']
        verbose_name = _('Врач')
        verbose_name_plural = _('Врачи')
        constraints = [
            models.UniqueConstraint(
                fields=['name', 'hospital'],
                name='unique_doctor_in_hospital'
            )
        ]
        indexes = [
            models.Index(fields=['specialization']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f'{self.name} - {self.specialization}'

    @property
    def full_title(self):
        return f"{self.name}, {self.specialization}"
    
    @property
    def upcoming_appointments(self):
        return self.appointments.filter(
            appointment_date__gte=timezone.now().date(),
            status='confirmed'
        )


class Patient(models.Model):
    is_active = models.BooleanField(default=True, verbose_name=_('Активен'))
    slug = models.SlugField(max_length=100, unique=True, blank=True, verbose_name=_('URL'))
    first_name = models.CharField(max_length=50, verbose_name=_("Имя"))
    last_name = models.CharField(max_length=50, verbose_name=_("Фамилия"))
    middle_name = models.CharField(max_length=50, blank=True, verbose_name=_("Отчество"))
    email = models.EmailField(max_length=200, unique=True, verbose_name=_("Email"))
    phone = models.CharField(max_length=20, verbose_name=_("Телефон"))
    address = models.CharField(max_length=200, verbose_name=_("Адрес"))
    date_of_birth = models.DateField(verbose_name=_("Дата рождения"))
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата регистрации"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))
    GENDER_CHOISES = [
        ('М', _('Мужской')),
        ('Ж', _('Женский'))
    ]
    gender = models.CharField(
        max_length=1,
        choices=GENDER_CHOISES,
        blank=True,
        verbose_name=_('Пол')
    )
    blood_type = models.CharField(
        max_length=5,
        blank=True,
        verbose_name=_('Группа крови'),
    )
    allergies = models.TextField(blank=True, verbose_name=_('Аллергии'))
    emergency_contact=models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Экстренный контакт'),
    )
    insurance_number = models.CharField(
        max_length=50,
        blank=True,
        verbose_name=_('Номер страховки')
    )

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(f"{self.last_name}-{self.first_name}")
            slug = base_slug
            counter = 1
            while Patient.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f'{base_slug}-{counter}'
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def clean(self):
        if self.date_of_birth > date.today():
            raise ValidationError(_("Дата рождения не может быть в будущем"))

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('model-detail', args=[str(self.id)])

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = _('Пациент')
        verbose_name_plural = _('Пациенты')
        indexes = [
            models.Index(fields=['last_name', 'first_name']),
            models.Index(fields=['email']),
            models.Index(fields=['phone']),
        ]

    def __str__(self):
        return f'{self.last_name} {self.first_name}'

    @property
    def full_name(self):
        if self.middle_name:
            return f'{self.last_name} {self.first_name} {self.middle_name}'
        return f'{self.last_name} {self.first_name}'

    @property
    def age(self):
        today = timezone.now().date()
        return today.year - self.date_of_birth.year - (
            (today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day)
        )
    
    @property
    def has_upcoming_appointments(self):
        return self.appointments.filter(is_upcoming=True).exists()


class Schedule(models.Model):
    DAYS_OF_WEEK = [
        (0, _('Понедельник')),
        (1, _('Вторник')),
        (2, _('Среда')),
        (3, _('Четверг')),
        (4, _('Пятница')),
        (5, _('Суббота')),
        (6, _('Воскресенье')),
    ]

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name=_('Врач')
    )
    cabinet = models.IntegerField(verbose_name=_('Номер кабинета'), validators=[MinValueValidator(1)])
    day_of_week = models.IntegerField(choices=DAYS_OF_WEEK, verbose_name=_("День недели"))
    start_time = models.TimeField(verbose_name=_("Время начала"))
    end_time = models.TimeField(verbose_name=_("Время окончания"))
    is_working = models.BooleanField(default=True, verbose_name=_("Рабочий день"))
    appointment_duration = models.IntegerField(
        default=30,
        validators=[MinValueValidator(10), MaxValueValidator(120)],
        verbose_name=_("Длительность приема (минут)")
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_("Дата создания"))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_("Дата обновления"))
    reception_type = models.CharField(max_length=10, 
                                      choices=[('offline','Оффлайн'), ('online','Онлайн')],
                                      default='offline'
                                      )
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('model-detail', args=[str(self.id)])

    class Meta:
        ordering = ['doctor', 'day_of_week']
        verbose_name = _('Расписание')
        verbose_name_plural = _('Расписания')
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'day_of_week'],
                name='unique_schedule_per_day'
            )
        ]
        indexes = [
            models.Index(fields=['day_of_week']),
            models.Index(fields=['is_working']),
        ]

    @property
    def available_slots(self):
        """Возвращает список доступных временных слотов"""
        from datetime import datetime, timedelta
        
        slots = []
        current = datetime.combine(datetime.today(), self.start_time)
        end = datetime.combine(datetime.today(), self.end_time)
        
        while current + timedelta(minutes=self.appointment_duration) <= end:
            slots.append(current.time())
            current += timedelta(minutes=self.appointment_duration)
        
        return slots

    def clean(self):
        if self.start_time >= self.end_time:
            raise ValidationError(_("Время начала должно быть раньше времени окончания"))

    def __str__(self):
        return f'{self.doctor.name} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}'
    


class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', _('Ожидает подтверждения')),
        ('confirmed', _('Подтверждена')),
        ('cancelled', _('Отменена')),
    ]

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('Пациент')
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name='appointments',
        verbose_name=_('Врач')
    )
    appointment_date = models.DateField(verbose_name=_('Дата приема'))
    appointment_time = models.TimeField(verbose_name=_("Время приема"))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_('Статус записи')
    )
    reason = models.TextField(blank=True, verbose_name=_("Причина обращения"))
    notes = models.TextField(blank=True, verbose_name=_('Примечания'))
    created_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Кем создана')
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Дата создания'))
    updated_at = models.DateTimeField(auto_now=True, verbose_name=_('Дата обновления'))
    price = models.FloatField(verbose_name=_('Стоимость приема'), null=True,blank=True, validators=[MinValueValidator(0)])
    reminder_sent = models.BooleanField(default=False, verbose_name=_('Напоминание отправлено'))

    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('model-detail', args=[str(self.id)])

    class Meta:
        ordering = ['appointment_date', 'appointment_time']
        verbose_name = _('Запись на прием')
        verbose_name_plural = _('Записи на прием')
        indexes = [
            models.Index(fields=['appointment_date', 'appointment_time']),
            models.Index(fields=['status']),
            models.Index(fields=['patient', 'doctor']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['doctor', 'appointment_date', 'appointment_time'],
                name='unique_appointment_time',
                condition=models.Q(status__in=['pending', 'confirmed'])
            )
        ]

    def clean(self):
        # Проверка на свободность записи
        if self.status in ['pending', 'confirmed']:
            conflicting_appointments = Appointment.objects.filter(
                doctor=self.doctor,
                appointment_date=self.appointment_date,
                appointment_time=self.appointment_time,
                status__in=['pending', 'confirmed']
            ).exclude(pk=self.pk if self.pk else None)

            if conflicting_appointments.exists():
                raise ValidationError(_('На это время уже есть запись к этому врачу'))

        # Проверка что дата приема не в прошлом
        if self.appointment_date < timezone.now().date():
            raise ValidationError(_('Нельзя записаться на прошедшую дату'))

        # Проверка что время приема соответствует расписанию врача
        if self.appointment_date:
            day_of_week = self.appointment_date.weekday()
            schedule = self.doctor.schedules.filter(day_of_week=day_of_week, is_working=True).first()
            if schedule:
                if not (schedule.start_time <= self.appointment_time <= schedule.end_time):
                    raise ValidationError(_('Время приема не входит в рабочие часы врача'))

    def send_reminder(self):
        if not self.reminder_sent and self.is_upcoming:
            try:
                # Логика отправки
                self.reminder_sent = True
                self.save(update_fields=['reminder_sent'])
                logger.info(f'Reminder sent for appointment {self.id}')
            except Exception as e:
                logger.error(f'Failed to send reminder: {e}')

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.patient.full_name} - {self.doctor.name} - {self.appointment_date} {self.appointment_time}'

    @property
    def is_upcoming(self):
        '''
        ПРОВЕРКА ПРОШЕЛ ЛИ ПРИЕМ
        '''
        appointment_datetime = timezone.make_aware(
            timezone.datetime.combine(self.appointment_date, self.appointment_time)
        )
        return appointment_datetime > timezone.now()

    @property
    def duration(self):
        '''
        ДЛИТЕЛЬНОСТЬ ПРИЕМА
        '''
        schedule = self.doctor.schedules.filter(
            day_of_week=self.appointment_date.weekday()
        ).first()
        return schedule.appointment_duration if schedule else 30
    

class MedicalRecord(models.Model):
    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name='medical_records',
        verbose_name=_('Пациент')
    )
    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.SET_NULL,
        null=True,
        verbose_name=_('Врач')
    )
    appointment = models.ForeignKey(
        Appointment,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name=_('Прием')
    )
    record_date = models.DateField(auto_now_add=True, verbose_name=_('Дата записи'))
    symptoms = models.TextField(verbose_name=_('Симптомы'))
    diagnosis = models.TextField(verbose_name=_('Диагноз'))
    treatment = models.TextField(verbose_name=_('Лечение'))
    cost = models.FloatField(verbose_name=_('Стоимость лечения'),
                              validators=[MinValueValidator(0)],
                              default=0 
                              )
    type_of_treatment = models.CharField(max_length=20, 
                                         choices=[('outpatient','Амбулаторное'),('inpatient','Стационарное')],
                                         default='outpatient'
                                         )
    
    def get_absolute_url(self):
        from django.urls import reverse
        return reverse('model-detail', args=[str(self.id)])
    
    class Meta:
        ordering = ['record_date']

    def __str__(self):
        patient_name = self.patient.full_name if self.patient else "Неизвестный пациент"
        return f'Медицинская запись: {patient_name} ({self.record_date})'