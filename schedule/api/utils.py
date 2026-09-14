def schedule_date(start_date, end_date, frequency):
    """
    Check if the start date is before the end date.
    """
    if end_date and start_date > end_date:
        return "End date must be after start date."

    if frequency != "ONCE" and not end_date:
        return "End date is required for recurring schedules."
    
    return None