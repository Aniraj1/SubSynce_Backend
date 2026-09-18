def schedule_date(start_date, end_date, frequency):
    """
    Check if the start date is before the end date.
    """
    if end_date and start_date > end_date:
        return "End date must be after start date."

    if frequency != "ONCE" and not end_date:
        return "End date is required for recurring schedules."
    
    return None



def occurrence_date(starts_at, ends_at):
    """
    Check if the start time is before the end time.
    """
    if ends_at <= starts_at:
        return "End time cannot be earlier than start time."

    return None