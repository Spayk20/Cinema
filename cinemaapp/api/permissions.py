from rest_framework import permissions


class CustomCinemaHallUpdatePermisson(permissions.BasePermission):
    message = 'You cannot change which hall is occupied'

    def has_object_permission(self, request, view, obj):
        if request.method in ['PATCH', 'PUT']:
            sessions = obj.sessions.filter(status=True)
            if sessions:
                for session in sessions:
                    if session.session_tickets.exists():
                        return False
        return True

    def has_permission(self, request, view):
        return True


class CustomSessionUpdatePermisson(permissions.BasePermission):
    message = 'You cannot change the session for which the ticket was purchased'

    def has_object_permission(self, request, view, obj):
        if request.method in ['PATCH', 'PUT']:
            if obj.session_tickets.exists():
                return False
        return True

    def has_permission(self, request, view):
        return True