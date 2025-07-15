from django.db import migrations
from django.db.models import Q

def migrate_teaching_monitoring_data(apps, schema_editor):
    """
    Migre les données des anciens champs vers les nouvelles relations
    """
    TeachingMonitoring = apps.get_model('Teaching', 'TeachingMonitoring')
    Lecturer = apps.get_model('Teaching', 'Lecturer')
    Course = apps.get_model('academic', 'Course')
    Level = apps.get_model('academic', 'Level')
    AcademicYear = apps.get_model('academic', 'AcademicYear')
    
    # Récupérer l'année académique active par défaut
    default_academic_year = AcademicYear.objects.filter(is_active=True).first()
    if not default_academic_year:
        default_academic_year = AcademicYear.objects.first()
    
    # Migrer chaque enregistrement
    for monitoring in TeachingMonitoring.objects.all():
        # Trouver l'enseignant correspondant
        if monitoring.nom and monitoring.prenom:
            lecturer = Lecturer.objects.filter(
                Q(firstname__icontains=monitoring.prenom) & 
                Q(lastname__icontains=monitoring.nom)
            ).first()
            
            if lecturer:
                monitoring.lecturer = lecturer
        
        # Trouver le cours correspondant
        if monitoring.intitule_cours:
            course = Course.objects.filter(
                label__icontains=monitoring.intitule_cours
            ).first()
            
            if course:
                monitoring.course = course
        
        # Trouver le niveau correspondant
        if monitoring.niveau is not None:
            level = Level.objects.filter(
                name__icontains=str(monitoring.niveau)
            ).first()
            
            if level:
                monitoring.level = level
        
        # Définir l'année académique par défaut
        monitoring.academic_year = default_academic_year
        
        # Sauvegarder les modifications
        monitoring.save()


class Migration(migrations.Migration):

    dependencies = [
        ('Teaching', '0004_alter_teachingmonitoring_options_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_teaching_monitoring_data, migrations.RunPython.noop),
    ]
