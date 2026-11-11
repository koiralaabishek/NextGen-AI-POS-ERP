from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status


def custom_exception_handler(exc, context):
    """
    Standardized API exception format across all NextGen endpoints.
    """
    response = exception_handler(exc, context)

    if response is not None:
        custom_data = {
            "success": False,
            "error": {
                "status_code": response.status_code,
                "message": getattr(exc, "detail", str(exc)),
                "type": exc.__class__.__name__,
            }
        }
        if isinstance(response.data, dict):
            custom_data["error"]["details"] = response.data
        elif isinstance(response.data, list):
            custom_data["error"]["details"] = {"non_field_errors": response.data}
        else:
            custom_data["error"]["details"] = str(response.data)

        response.data = custom_data

    return response
