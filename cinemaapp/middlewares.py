from django.contrib.auth import logout
from django.utils.deprecation import MiddlewareMixin
from django.shortcuts import redirect
from datetime import timedelta, datetime
from django.utils import timezone


class TimeActionMiddleware(MiddlewareMixin):
    def process_request(self, request):
        if 'time_action' in request.session:
            date = datetime.strptime(request.session['time_action'], '%Y-%m-%d %H:%M:%S.%f')
            if not request.user.is_superuser and date + timedelta(minutes=5) < timezone.now():
                logout(request)
                return redirect('/login/')
            else:
                request.session['time_action'] = str(timezone.now())
