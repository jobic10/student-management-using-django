from django.utils.deprecation import MiddlewareMixin
from django.urls import reverse
from django.contrib.auth import logout
from django.shortcuts import redirect


# Which user_type is allowed to reach views defined in each module.
MODULE_ROLES = {
    'main_app.hod_views': '1',
    'main_app.staff_views': '2',
    'main_app.student_views': '3',
}

# Modules whose views are reachable by any authenticated user. Views in these
# modules MUST perform their own role / ownership checks.
SHARED_MODULES = {
    'main_app.views',
}

ROLE_HOME = {
    '1': 'admin_home',
    '2': 'staff_home',
    '3': 'student_home',
}


class LoginCheckMiddleWare(MiddlewareMixin):
    def process_view(self, request, view_func, view_args, view_kwargs):
        modulename = view_func.__module__
        user = request.user  # Who is the current user ?
        if user.is_authenticated:
            home = ROLE_HOME.get(user.user_type)
            if home is None:  # Unknown role, end the session
                logout(request)
                return redirect(reverse('login_page'))
            required_role = MODULE_ROLES.get(modulename)
            if required_role is not None:
                if user.user_type != required_role:
                    return redirect(reverse(home))
            elif modulename.startswith('main_app.') and modulename not in SHARED_MODULES:
                # Deny by default: any app module that has not been explicitly
                # mapped to a role must not be reachable.
                return redirect(reverse(home))
        else:
            if request.path == reverse('login_page') or modulename == 'django.contrib.auth.views' or request.path == reverse('user_login'): # If the path is login or has anything to do with authentication, pass
                pass
            else:
                return redirect(reverse('login_page'))
