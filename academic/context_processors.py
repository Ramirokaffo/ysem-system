from academic.models import AcademicYear

def active_academic_year(request):
    """
    Context processor pour injecter l'année académique active dans tous les templates.
    """
    year_id = request.session.get('active_academic_year_id')
    active_year = None

    if year_id:
        try:
            active_year = AcademicYear.objects.get(id=year_id)
            
        except AcademicYear.DoesNotExist:
            active_year = None
    else:
        try:
            active_year = AcademicYear.objects.filter(is_active=True).first()
            if active_year:
                request.session['active_academic_year_id'] = active_year.id
        except AcademicYear.DoesNotExist:
            active_year = None
    return {'active_academic_year': active_year}
