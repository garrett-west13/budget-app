from datetime import datetime

def default_year_month(request):
    current_date = datetime.now()
    default_year = current_date.year
    default_month = current_date.month
    return {
        'default_year': default_year,
        'default_month': default_month,
    }
