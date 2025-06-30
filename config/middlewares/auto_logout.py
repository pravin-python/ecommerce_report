from django.utils.deprecation import MiddlewareMixin
from django.conf import settings
from django.shortcuts import redirect
import datetime

class AutoLogout(MiddlewareMixin):
    def process_request(self, request):
        if not request.user.is_authenticated:
            return

        try:
            last_activity = request.session['last_activity']
            now = datetime.datetime.now().timestamp()
            if now - last_activity > 10800:
                from django.contrib.auth import logout
                logout(request)
                return redirect('login')
        except KeyError:
            pass

        request.session['last_activity'] = datetime.datetime.now().timestamp()
