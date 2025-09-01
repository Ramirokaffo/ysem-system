from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import datetime, timedelta
from Teaching.models import Lecturer
from academic.models import Course, Level, AcademicYear


class Floor(models.Model):
    """
    Modèle pour les étage
    """
    number = models.IntegerField(max_length=20, primary_key=True, verbose_name="Numéro étage")
    name = models.CharField(max_length=100, verbose_name="Nom d'étage")

    def __str__(self):
        return f"{self.number} - {self.name}"

    class Meta:
        verbose_name = "Etage"
        verbose_name_plural = "Etages"
        ordering = ['number']

class Building(models.Model):
    """
    Modèle pour les batiments
    """
    code = models.CharField(max_length=20, primary_key=True, verbose_name="Code du batiment")
    name = models.CharField(max_length=100, verbose_name="Nom du batiment")

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Batiment"
        verbose_name_plural = "Batiments"
        ordering = ['code']

class Equipment(models.Model):
    """
    Modèle pour les équipements
    """
    code = models.CharField(max_length=20, primary_key=True, verbose_name="Code de l'équipement")
    name = models.CharField(max_length=100, verbose_name="Nom de l'équipement")

    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Equipement"
        verbose_name_plural = "Equipements"
        ordering = ['code']

class Classroom(models.Model):
    """
    Modèle pour les salles de classe
    """
    code = models.CharField(max_length=20, primary_key=True, verbose_name="Code de la salle")
    name = models.CharField(max_length=100, verbose_name="Nom de la salle")
    capacity = models.IntegerField(
        validators=[MinValueValidator(1)],
        verbose_name="Capacité"
    )
    building = models.CharField(max_length=100, blank=True, null=True, verbose_name="Bâtiment")
    floor = models.CharField(max_length=20, blank=True, null=True, verbose_name="Étage")
    equipment = models.ManyToManyField(Equipment, blank=True, null=True, verbose_name="Équipements disponibles")
    is_active = models.BooleanField(default=True, verbose_name="Salle active")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")
    deleted_at =  models.DateTimeField(auto_now=True, verbose_name="Date de suppression")
    
    def __str__(self):
        return f"{self.code} - {self.name}"

    class Meta:
        verbose_name = "Salle de classe"
        verbose_name_plural = "Salles de classe"
        ordering = ['code']





class TimeSlot(models.Model):
    """
    Modèle pour les créneaux horaires
    """
    DAYS_OF_WEEK = [
        ('monday', 'Lundi'),
        ('tuesday', 'Mardi'),
        ('wednesday', 'Mercredi'),
        ('thursday', 'Jeudi'),
        ('friday', 'Vendredi'),
        ('saturday', 'Samedi'),
        ('sunday', 'Dimanche'),
    ]

    name = models.CharField(max_length=100, verbose_name="Nom du créneau")
    day_of_week = models.CharField(max_length=10, choices=DAYS_OF_WEEK, verbose_name="Jour de la semaine")
    start_time = models.TimeField(verbose_name="Heure de début")
    end_time = models.TimeField(verbose_name="Heure de fin")
    is_active = models.BooleanField(default=True, verbose_name="Créneau actif")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def duration_hours(self):
        """Retourne la durée du créneau en heures"""
        if self.start_time and self.end_time:
            from datetime import datetime
            start_datetime = datetime.combine(datetime.today(), self.start_time)
            end_datetime = datetime.combine(datetime.today(), self.end_time)
            duration = end_datetime - start_datetime
            return round(duration.total_seconds() / 3600, 1)
        return 0

    def __str__(self):
        return f"{self.get_day_of_week_display()} {self.start_time}-{self.end_time}"

    class Meta:
        verbose_name = "Créneau horaire"
        verbose_name_plural = "Créneaux horaires"
        ordering = ['day_of_week', 'start_time']
        unique_together = ['day_of_week', 'start_time', 'end_time']


class CourseSession(models.Model):
    """
    Modèle pour les séances de cours
    """
    SESSION_TYPES = [
        ('lecture', 'Cours magistral'),
        ('tutorial', 'Travaux dirigés'),
        ('practical', 'Travaux pratiques'),
        ('exam', 'Examen'),
        ('other', 'Autre'),
    ]

    SESSION_STATUS = [
        ('scheduled', 'Programmée'),
        ('ongoing', 'En cours'),
        ('completed', 'Terminée'),
        ('cancelled', 'Annulée'),
        ('postponed', 'Reportée'),
    ]

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Cours"
    )
    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Enseignant"
    )
    classroom = models.ForeignKey(
        Classroom,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Salle de classe"
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Créneau horaire"
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Niveau"
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='sessions',
        verbose_name="Année académique"
    )
    session_type = models.CharField(
        max_length=20,
        choices=SESSION_TYPES,
        default='lecture',
        verbose_name="Type de séance"
    )
    status = models.CharField(
        max_length=20,
        choices=SESSION_STATUS,
        default='scheduled',
        verbose_name="Statut"
    )
    date = models.DateField(verbose_name="Date de la séance")
    duration_hours = models.DecimalField(
        max_digits=3,
        decimal_places=1,
        default=1.5,
        validators=[MinValueValidator(0.5), MaxValueValidator(8.0)],
        verbose_name="Durée (heures)"
    )
    topic = models.CharField(max_length=200, blank=True, null=True, verbose_name="Sujet/Chapitre")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    attendance_count = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Nombre de présents"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def __str__(self):
        return f"{self.course.label} - {self.date} ({self.time_slot})"

    class Meta:
        verbose_name = "Séance de cours"
        verbose_name_plural = "Séances de cours"
        ordering = ['-date', 'time_slot__start_time']
        unique_together = ['classroom', 'time_slot', 'date']


class Schedule(models.Model):
    """
    Modèle pour les emplois du temps
    """
    DURATION_CHOICES = [
        ('1_month', '1 mois'),
        ('3_months', '3 mois'),
        ('6_months', '6 mois'),
        ('1_year', '1 année'),
        ('custom', 'Personnalisé'),
    ]

    STATUS_CHOICES = [
        ('draft', 'Brouillon'),
        ('active', 'Actif'),
        ('archived', 'Archivé'),
    ]

    name = models.CharField(max_length=200, verbose_name="Nom de l'emploi du temps")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name="Année académique"
    )
    level = models.ForeignKey(
        Level,
        on_delete=models.CASCADE,
        related_name='schedules',
        verbose_name="Niveau"
    )
    start_date = models.DateField(verbose_name="Date de début")
    end_date = models.DateField(verbose_name="Date de fin")
    duration_type = models.CharField(
        max_length=20,
        choices=DURATION_CHOICES,
        default='3_months',
        verbose_name="Type de durée"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
        verbose_name="Statut"
    )
    is_generated = models.BooleanField(
        default=False,
        verbose_name="Généré automatiquement"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")

            # Vérifier que les dates sont dans l'année académique
            if (self.start_date < self.academic_year.start_at or
                self.end_date > self.academic_year.end_at):
                raise ValidationError(
                    "Les dates doivent être comprises dans l'année académique sélectionnée."
                )

    def get_duration_days(self):
        """Retourne la durée en jours"""
        if self.start_date and self.end_date:
            return (self.end_date - self.start_date).days
        return 0

    def get_total_sessions(self):
        """Retourne le nombre total de séances dans cet emploi du temps"""
        return self.schedule_sessions.count()

    def __str__(self):
        return f"{self.name} - {self.level.name} ({self.academic_year})"

    class Meta:
        verbose_name = "Emploi du temps"
        verbose_name_plural = "Emplois du temps"
        ordering = ['-created_at']
        unique_together = ['name', 'academic_year', 'level']


class LecturerAvailability(models.Model):
    """
    Modèle pour la disponibilité des enseignants
    """
    AVAILABILITY_STATUS = [
        ('available', 'Disponible'),
        ('unavailable', 'Indisponible'),
        ('preferred', 'Préféré'),
    ]

    lecturer = models.ForeignKey(
        Lecturer,
        on_delete=models.CASCADE,
        related_name='availabilities',
        verbose_name="Enseignant"
    )
    time_slot = models.ForeignKey(
        TimeSlot,
        on_delete=models.CASCADE,
        related_name='lecturer_availabilities',
        verbose_name="Créneau horaire"
    )
    academic_year = models.ForeignKey(
        AcademicYear,
        on_delete=models.CASCADE,
        related_name='lecturer_availabilities',
        verbose_name="Année académique"
    )
    status = models.CharField(
        max_length=20,
        choices=AVAILABILITY_STATUS,
        default='available',
        verbose_name="Statut de disponibilité"
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de début (optionnel)"
    )
    end_date = models.DateField(
        blank=True,
        null=True,
        verbose_name="Date de fin (optionnel)"
    )
    notes = models.TextField(
        blank=True,
        null=True,
        verbose_name="Notes"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")
    last_updated = models.DateTimeField(auto_now=True, verbose_name="Dernière mise à jour")

    def clean(self):
        if self.start_date and self.end_date:
            if self.start_date >= self.end_date:
                raise ValidationError("La date de fin doit être postérieure à la date de début.")

    def is_available_on_date(self, date):
        """Vérifie si l'enseignant est disponible à une date donnée"""
        if self.status == 'unavailable':
            return False

        if self.start_date and self.end_date:
            return self.start_date <= date <= self.end_date

        return True

    def __str__(self):
        return f"{self.lecturer} - {self.time_slot} ({self.get_status_display()})"

    class Meta:
        verbose_name = "Disponibilité enseignant"
        verbose_name_plural = "Disponibilités enseignants"
        ordering = ['lecturer__lastname', 'time_slot__day_of_week', 'time_slot__start_time']
        unique_together = ['lecturer', 'time_slot', 'academic_year', 'start_date', 'end_date']


class ScheduleSession(models.Model):
    """
    Modèle pour lier les emplois du temps aux séances de cours
    """
    schedule = models.ForeignKey(
        Schedule,
        on_delete=models.CASCADE,
        related_name='schedule_sessions',
        verbose_name="Emploi du temps"
    )
    course_session = models.ForeignKey(
        CourseSession,
        on_delete=models.CASCADE,
        related_name='schedule_sessions',
        verbose_name="Séance de cours"
    )
    week_number = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(52)],
        verbose_name="Numéro de semaine"
    )
    is_recurring = models.BooleanField(
        default=True,
        verbose_name="Séance récurrente"
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Date de création")

    def __str__(self):
        return f"{self.schedule.name} - {self.course_session} (Semaine {self.week_number})"

    class Meta:
        verbose_name = "Séance d'emploi du temps"
        verbose_name_plural = "Séances d'emploi du temps"
        ordering = ['week_number', 'course_session__time_slot__day_of_week', 'course_session__time_slot__start_time']
        unique_together = ['schedule', 'course_session']
