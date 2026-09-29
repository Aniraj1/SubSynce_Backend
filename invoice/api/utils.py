
from datetime import date

def filter_invoices_by_date_range(invoices, start_date, end_date):
    """
    Filters the invoices based on the provided start and end dates.

    Args:
        invoices (QuerySet): The queryset of invoices to filter.
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.
    """
    if start_date:
        invoices = invoices.filter(invoice_date__gte=date.fromisoformat(start_date))
    
    if end_date:
        invoices = invoices.filter(invoice_date__lte=date.fromisoformat(end_date))
    
    if start_date and end_date and date.fromisoformat(start_date) > date.fromisoformat(end_date):
        return "Start date cannot be after end date."

    return invoices


def check_date_format(start_date, end_date):
    """
    Checks if the provided date string is in the correct 'YYYY-MM-DD' format.

    Args:
        date_str (str): The date string to check.
    Returns:
        bool: True if the date string is in the correct format, False otherwise.
    """

    try:
        if start_date:
            date.fromisoformat(start_date)

        if end_date:
            date.fromisoformat(end_date)

        return True

    except (ValueError, TypeError):
        return False