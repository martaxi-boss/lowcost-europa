from django.db import DatabaseError, OperationalError, connection
from django.http import JsonResponse


def live(request):
    return JsonResponse({"status": "ok"})


def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            cursor.fetchone()
    except (OperationalError, DatabaseError):
        return JsonResponse({"status": "unavailable"}, status=503)
    return JsonResponse({"status": "ok"})
