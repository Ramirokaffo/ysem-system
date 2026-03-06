"""
Services pour la génération automatique d'emploi du temps
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from datetime import datetime, timedelta
import random
from collections import defaultdict

from .models import (
    Schedule, CourseSession, ScheduleSession, TimeSlot, 
    Classroom, LecturerAvailability
)
from Teaching.models import Lecturer
from academic.models import Course


class ScheduleGenerationService:
    """
    Service pour la génération automatique d'emploi du temps
    """
    
    def __init__(self, schedule, courses, sessions_per_week=2, 
                 prefer_morning=True, avoid_consecutive_sessions=True, 
                 max_daily_sessions=4):
        self.schedule = schedule
        self.courses = courses
        self.sessions_per_week = sessions_per_week
        self.prefer_morning = prefer_morning
        self.avoid_consecutive_sessions = avoid_consecutive_sessions
        self.max_daily_sessions = max_daily_sessions
        
        # Structures de données pour la génération
        self.available_time_slots = []
        self.available_classrooms = []
        self.lecturer_availabilities = {}
        self.generated_sessions = []
        self.weekly_schedule = defaultdict(list)  # {week_number: [sessions]}
        
    def generate_schedule(self):
        """
        Génère automatiquement l'emploi du temps
        """
        try:
            with transaction.atomic():
                # 1. Préparer les données
                self._prepare_data()
                
                # 2. Valider la faisabilité
                self._validate_feasibility()
                
                # 3. Générer les séances
                self._generate_sessions()
                
                # 4. Sauvegarder les résultats
                self._save_generated_sessions()
                
                # 5. Marquer l'emploi du temps comme généré
                self.schedule.is_generated = True
                self.schedule.status = 'active'
                self.schedule.save()
                
                return {
                    'success': True,
                    'message': f'Emploi du temps généré avec succès. {len(self.generated_sessions)} séances créées.',
                    'sessions_count': len(self.generated_sessions)
                }
                
        except Exception as e:
            return {
                'success': False,
                'message': f'Erreur lors de la génération: {str(e)}',
                'sessions_count': 0
            }
    
    def _prepare_data(self):
        """
        Prépare les données nécessaires pour la génération
        """
        # Récupérer les créneaux horaires disponibles (lundi à vendredi)
        self.available_time_slots = list(
            TimeSlot.objects.filter(
                is_active=True,
                day_of_week__in=['monday', 'tuesday', 'wednesday', 'thursday', 'friday']
            ).order_by('day_of_week', 'start_time')
        )
        
        # Trier par préférence (matin en premier si demandé)
        if self.prefer_morning:
            self.available_time_slots.sort(key=lambda ts: (ts.day_of_week, ts.start_time))
        
        # Récupérer les salles disponibles
        self.available_classrooms = list(
            Classroom.objects.filter(is_active=True).order_by('capacity')
        )
        
        # Récupérer les disponibilités des enseignants
        availabilities = LecturerAvailability.objects.filter(
            academic_year=self.schedule.academic_year,
            status__in=['available', 'preferred']
        ).select_related('lecturer', 'time_slot')
        
        for availability in availabilities:
            lecturer_id = availability.lecturer.matricule
            time_slot_id = availability.time_slot.id
            
            if lecturer_id not in self.lecturer_availabilities:
                self.lecturer_availabilities[lecturer_id] = {}
            
            self.lecturer_availabilities[lecturer_id][time_slot_id] = availability
    
    def _validate_feasibility(self):
        """
        Valide la faisabilité de la génération
        """
        total_sessions_needed = len(self.courses) * self.sessions_per_week
        total_weeks = self._get_total_weeks()
        
        # Vérifier qu'il y a assez de créneaux
        available_slots_per_week = len(self.available_time_slots)
        max_sessions_per_week = min(available_slots_per_week, self.max_daily_sessions * 5)
        
        if total_sessions_needed > max_sessions_per_week:
            raise ValidationError(
                f"Impossible de programmer {total_sessions_needed} séances par semaine. "
                f"Maximum possible: {max_sessions_per_week}"
            )
        
        # Vérifier qu'il y a des salles disponibles
        if not self.available_classrooms:
            raise ValidationError("Aucune salle de classe disponible.")
        
        # Vérifier qu'il y a des créneaux disponibles
        if not self.available_time_slots:
            raise ValidationError("Aucun créneau horaire disponible.")
    
    def _generate_sessions(self):
        """
        Génère les séances de cours
        """
        total_weeks = self._get_total_weeks()
        
        for week_number in range(1, total_weeks + 1):
            self._generate_week_sessions(week_number)
    
    def _generate_week_sessions(self, week_number):
        """
        Génère les séances pour une semaine donnée
        """
        week_sessions = []
        used_time_slots = set()
        
        for course in self.courses:
            sessions_created = 0
            attempts = 0
            max_attempts = 50
            
            while sessions_created < self.sessions_per_week and attempts < max_attempts:
                attempts += 1
                
                # Sélectionner un créneau disponible
                available_slots = [
                    ts for ts in self.available_time_slots 
                    if ts.id not in used_time_slots
                ]
                
                if not available_slots:
                    break
                
                time_slot = self._select_best_time_slot(course, available_slots, week_sessions)
                if not time_slot:
                    continue
                
                # Trouver un enseignant disponible
                lecturer = self._find_available_lecturer(course, time_slot)
                if not lecturer:
                    continue
                
                # Trouver une salle disponible
                classroom = self._find_available_classroom(time_slot, week_number)
                if not classroom:
                    continue
                
                # Créer la séance
                session_date = self._get_session_date(week_number, time_slot.day_of_week)
                session = self._create_session(
                    course, lecturer, classroom, time_slot, session_date, week_number
                )
                
                week_sessions.append(session)
                used_time_slots.add(time_slot.id)
                sessions_created += 1
        
        self.weekly_schedule[week_number] = week_sessions
        self.generated_sessions.extend(week_sessions)
    
    def _select_best_time_slot(self, course, available_slots, existing_sessions):
        """
        Sélectionne le meilleur créneau pour un cours
        """
        if not available_slots:
            return None
        
        # Si on évite les séances consécutives, filtrer
        if self.avoid_consecutive_sessions:
            course_sessions_today = [
                s for s in existing_sessions 
                if s['course'] == course
            ]
            
            if course_sessions_today:
                # Éviter les créneaux adjacents
                used_slots = [s['time_slot'] for s in course_sessions_today]
                available_slots = [
                    ts for ts in available_slots
                    if not self._is_adjacent_time_slot(ts, used_slots)
                ]
        
        if not available_slots:
            return None
        
        # Privilégier les créneaux préférés si disponibles
        preferred_slots = []
        for time_slot in available_slots:
            for lecturer_id, availabilities in self.lecturer_availabilities.items():
                if time_slot.id in availabilities:
                    availability = availabilities[time_slot.id]
                    if availability.status == 'preferred':
                        preferred_slots.append(time_slot)
                        break
        
        if preferred_slots:
            return random.choice(preferred_slots)
        
        return random.choice(available_slots)
    
    def _find_available_lecturer(self, course, time_slot):
        """
        Trouve un enseignant disponible pour un cours et un créneau
        """
        # Pour cette version simplifiée, on prend le premier enseignant disponible
        # Dans une version plus avancée, on pourrait avoir une relation Course-Lecturer
        available_lecturers = []
        
        for lecturer_id, availabilities in self.lecturer_availabilities.items():
            if time_slot.id in availabilities:
                availability = availabilities[time_slot.id]
                if availability.status in ['available', 'preferred']:
                    try:
                        lecturer = Lecturer.objects.get(matricule=lecturer_id)
                        available_lecturers.append(lecturer)
                    except Lecturer.DoesNotExist:
                        continue
        
        if available_lecturers:
            return random.choice(available_lecturers)
        
        # Si aucun enseignant spécifiquement disponible, prendre le premier
        return Lecturer.objects.first()
    
    def _find_available_classroom(self, time_slot, week_number):
        """
        Trouve une salle disponible pour un créneau
        """
        session_date = self._get_session_date(week_number, time_slot.day_of_week)
        
        # Vérifier les salles non occupées à cette date et ce créneau
        occupied_classrooms = CourseSession.objects.filter(
            date=session_date,
            time_slot=time_slot
        ).values_list('classroom_id', flat=True)
        
        available_classrooms = [
            classroom for classroom in self.available_classrooms
            if classroom.code not in occupied_classrooms
        ]
        
        if available_classrooms:
            return available_classrooms[0]  # Prendre la première disponible
        
        return None
    
    def _create_session(self, course, lecturer, classroom, time_slot, session_date, week_number):
        """
        Crée une structure de données pour une séance
        """
        return {
            'course': course,
            'lecturer': lecturer,
            'classroom': classroom,
            'time_slot': time_slot,
            'date': session_date,
            'week_number': week_number,
            'level': self.schedule.level,
            'academic_year': self.schedule.academic_year
        }
    
    def _save_generated_sessions(self):
        """
        Sauvegarde les séances générées en base de données
        """
        for session_data in self.generated_sessions:
            # Créer la séance de cours
            course_session = CourseSession.objects.create(
                course=session_data['course'],
                lecturer=session_data['lecturer'],
                classroom=session_data['classroom'],
                time_slot=session_data['time_slot'],
                level=session_data['level'],
                academic_year=session_data['academic_year'],
                date=session_data['date'],
                session_type='lecture',
                status='scheduled'
            )
            
            # Lier à l'emploi du temps
            ScheduleSession.objects.create(
                schedule=self.schedule,
                course_session=course_session,
                week_number=session_data['week_number'],
                is_recurring=True
            )
    
    def _get_total_weeks(self):
        """
        Calcule le nombre total de semaines dans la période
        """
        delta = self.schedule.end_date - self.schedule.start_date
        return max(1, delta.days // 7)
    
    def _get_session_date(self, week_number, day_of_week):
        """
        Calcule la date d'une séance basée sur la semaine et le jour
        """
        days_mapping = {
            'monday': 0, 'tuesday': 1, 'wednesday': 2, 
            'thursday': 3, 'friday': 4
        }
        
        start_date = self.schedule.start_date
        days_to_add = (week_number - 1) * 7 + days_mapping[day_of_week]
        
        return start_date + timedelta(days=days_to_add)
    
    def _is_adjacent_time_slot(self, time_slot, used_slots):
        """
        Vérifie si un créneau est adjacent à des créneaux utilisés
        """
        for used_slot in used_slots:
            if (time_slot.day_of_week == used_slot.day_of_week and
                abs((time_slot.start_time.hour - used_slot.start_time.hour)) <= 2):
                return True
        return False
