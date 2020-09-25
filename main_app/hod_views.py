from django.shortcuts import render, redirect
from .models import *
from django.contrib import messages


def admin_home(request):
    return render(request, 'hod_template/home_content.html')


def add_staff(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        username = request.POST.get('username')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        course_id = request.POST.get('course')
        try:
            course = Course.objects.get(id=course_id)
            user = CustomUser.objects.create_user(
                username=username, email=email, password=password, user_type=2, first_name=first_name, last_name=last_name)
            user.staff.gender = gender
            user.staff.address = address
            user.staff.course = course
            user.save()
            messages.success(request, "Successfully Added")
            return redirect('/add_staff/')
        except Exception as e:
            messages.warning(request, "Could Not Add " + str(e))
            return redirect('/add_staff/')
    context = {
        'courses': Course.objects.all()
    }
    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        username = request.POST.get('username')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        password = request.POST.get('password')
        course_id = request.POST.get('course')
        session_start = request.POST.get('session_start')
        session_end = request.POST.get('session_end')

        try:
            course = Course.objects.get(id=course_id)

            user = CustomUser.objects.create_user(
                username=username, email=email, password=password, user_type=3, first_name=first_name, last_name=last_name)
            user.student.gender = gender
            user.student.address = address
            user.student.session_start_year = session_start
            user.student.session_end_year = session_end
            user.student.course = course
            user.save()
            messages.success(request, "Successfully Added")
            return redirect('/add_student/')
        except Exception as e:
            messages.warning(request, "Could Not Add: " + str(e))
            return redirect('/add_student/')
    context = {
        'courses': Course.objects.all()
    }
    return render(request, 'hod_template/add_student_template.html', context)


def add_course(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        try:
            course = Course()
            course.name = name
            course.save()
            messages.success(request, "Successfully Added")
            return redirect('/add_course/')
        except:
            messages.warning(request, "Could Not Add")
            return redirect('/add_course/')
    return render(request, 'hod_template/add_course_template.html')


def add_subject(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        course_id = request.POST.get('course')
        staff_id = request.POST.get('staff')
        print(f'I got back {course_id} and {staff_id} ')
        try:
            course = Course.objects.get(id=course_id)
            staff = CustomUser.objects.get(id=staff_id)
            subject = Subject()
            subject.name = name
            subject.staff = staff
            subject.course = course
            subject.save()
            print(f'I got back {course.name} and {staff.first_name} ')
            messages.success(request, "Successfully Added")
            return redirect('/add_subject/')
        except Exception as e:
            messages.warning(request, "Could Not Add " + str(e))
            return redirect('/add_subject/')
    context = {
        'courses': Course.objects.all(),
        'staff': CustomUser.objects.filter(user_type=2)
    }
    return render(request, 'hod_template/add_subject_template.html', context)


def manage_staff(request):
    allStaff = CustomUser.objects.filter(user_type=2)
    context = {
        'allStaff': allStaff
    }
    return render(request, "hod_template/manage_staff.html", context)
