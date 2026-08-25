from rest_framework.response import Response


def project_return(message=None, data=None, error=None, status=None):
    return Response(
        {"message": message, "data": data, "status": status, "error": error},
        status=status,
    )