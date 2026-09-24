
from datetime import date, timedelta

def filter_work_by_period(work_obj, period):
    """
    Filter work based on the specified period (daily, weekly, fortnightly).
    """

    if not period:
        return None

    today = date.today()
    period = period.lower()
    current_week_start = today - timedelta(days=today.weekday())
    current_week_end = current_week_start + timedelta(days=6)
    previous_week_start = current_week_start - timedelta(days=7)
    if period == "today":
        work_obj = work_obj.filter(
            schedule__scheduled_date=today
        )
        return work_obj

    
    if period == "weekly":
        work_obj = work_obj.filter(
            schedule__scheduled_date__range=[
                current_week_start,
                current_week_end,
            ]
        )
        return work_obj


    return None