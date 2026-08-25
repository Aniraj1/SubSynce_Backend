import traceback

from rest_framework.exceptions import NotAuthenticated
from rest_framework.views import exception_handler

from globalutils.returnobject import project_return



def custom_exception_handler(exc, context):
    response = exception_handler(exc, context)

    tb = traceback.extract_tb(exc.__traceback__)

    line_number = tb[-1].lineno
    file_name = tb[-1].filename

    if not response:

        return project_return(
            message="Server error",
            error=str(exc),
            status=500,
        )
    if isinstance(exc, NotAuthenticated) or response.status_code == 401:
        return project_return(
            message=response.data.get("code")
            if response.data.get("code")
            else "Not authenticated",
            error=response.data.get("detail"),
            status=401,
        )
    if response.status_code == 400:
        return project_return(
            message=response.data.get("code"),
            error=response.data.get("detail"),
            status=400,
        )
    if response.status_code == 403:
        return project_return(
            message=response.data.get("code"),
            error=response.data.get("detail"),
            status=403,
        )
    if response.status_code == 429:
        return project_return(
            message=response.data.get("code"),
            error=response.data.get("detail"),
            status=429,
        )
    return exception_handler(exc, context)
