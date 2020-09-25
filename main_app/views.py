from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.contrib.auth import logout, login, authenticate
from .EmailBackend import EmailBackend
from django.contrib import messages
# Create your views here.


def login_page(request):
    return render(request, 'main_app/login.html')


def doLogin(request, **kwargs):
    if request.method != 'POST':
        return HttpResponse("<h4>Denied</h4>")
    else:
        user = EmailBackend.authenticate(request, username=request.POST.get(
            'email'), password=request.POST.get('password'))
        if user != None:
            login(request, user)
            print(user.user_type)
            if user.user_type == '1':
                return redirect("/admin_home/")
            elif user.user_type == '2':
                return HttpResponse("Staff")
            else:
                return HttpResponse("Student")
        else:
            messages.error(request, "Invalid details")
            return redirect("/")


def getUserDetails(request):
    if request.user != None:
        return HttpResponse("User: " + request.user.email + "User Type " + request.user.user_type)
    else:
        return HttpResponse("Please Login")


def logout_user(request):
    if request.user != None:
        logout(request)
    return redirect("/")
