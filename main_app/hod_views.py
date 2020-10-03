from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse
from django.views.generic import UpdateView

from .forms import *
from .models import *


def admin_home(request):
    return render(request, 'hod_template/home_content.html')


def add_staff(request):
    form = StaffForm(request.POST or None, request.FILES or None)
    context = {'form': form}
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password')
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic')
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=2, first_name=first_name, last_name=last_name)
                user.staff.gender = gender
                user.staff.address = address
                user.staff.profile_pic = passport_url
                user.staff.course = course
                user.save()
                messages.success(request, "Successfully Added")
                return render(request, 'hod_template/add_staff_template.html', {'form': StaffForm()})

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
                return render(request, 'hod_template/add_staff_template.html', context)
        else:
            messages.error(request, "Please fulfil all requirements")
            return render(request, 'hod_template/add_staff_template.html', context)

    return render(request, 'hod_template/add_staff_template.html', context)


def add_student(request):
    student_form = StudentForm(request.POST or None, request.FILES or None)
    context = {'form': student_form}
    if request.method == 'POST':
        if student_form.is_valid():
            first_name = student_form.cleaned_data.get('first_name')
            last_name = student_form.cleaned_data.get('last_name')
            address = student_form.cleaned_data.get('address')
            email = student_form.cleaned_data.get('email')
            gender = student_form.cleaned_data.get('gender')
            password = student_form.cleaned_data.get('password')
            course = student_form.cleaned_data.get('course')
            session = student_form.cleaned_data.get('session')
            passport = request.FILES['profile_pic']
            fs = FileSystemStorage()
            filename = fs.save(passport.name, passport)
            passport_url = fs.url(filename)
            try:
                user = CustomUser.objects.create_user(
                    email=email, password=password, user_type=3, first_name=first_name, last_name=last_name)
                user.student.gender = gender
                user.student.address = address
                user.student.profile_pic = passport_url
                user.student.session = session
                user.student.course = course
                user.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_student'))
            except Exception as e:
                messages.error(request, "Could Not Add: " + str(e))
                return render(request, 'hod_template/add_student_template.html', context)
        else:
            messages.error(request, "Could Not Add: ")
            return render(request, 'hod_template/add_student_template.html', context)
    return render(request, 'hod_template/add_student_template.html', context)


def add_course(request):
    form = CourseForm(request.POST or None)
    context = {
        'form': form
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course()
                course.name = name
                course.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_course'))
                return render(request, 'hod_template/add_course_template.html')
            except:
                messages.error(request, "Could Not Add")
                return render(request, 'hod_template/add_course_template.html', context)
        else:
            messages.error(request, "Could Not Add")
            return render(request, 'hod_template/add_course_template.html', context)
    return render(request, 'hod_template/add_course_template.html', context)


def add_subject(request):
    form = SubjectForm(request.POST or None)
    context = {
        'form': form
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject()
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('add_subject'))

            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
                return render(request, 'hod_template/add_subject_template.html', context)

        else:
            messages.error(request, "Fill Form Properly")
            return render(request, 'hod_template/add_subject_template.html', context)

    return render(request, 'hod_template/add_subject_template.html', context)


def manage_staff(request):
    allStaff = CustomUser.objects.filter(user_type=2)
    context = {
        'allStaff': allStaff
    }
    return render(request, "hod_template/manage_staff.html", context)


def manage_student(request):
    students = CustomUser.objects.filter(user_type=3)
    context = {
        'students': students
    }
    return render(request, "hod_template/manage_student.html", context)


def manage_course(request):
    courses = Course.objects.all()
    context = {
        'courses': courses
    }
    return render(request, "hod_template/manage_course.html", context)


def manage_subject(request):
    subjects = Subject.objects.all()
    context = {
        'subjects': subjects
    }
    return render(request, "hod_template/manage_subject.html", context)


def edit_staff(request, staff_id):
    instance = get_object_or_404(Staff, id=staff_id)
    form = StaffForm(request.POST or None, instance=instance)
    context = {
        'form': form
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            passport = request.FILES.get('profile_pic') or None
            try:
                staff = Staff.objects.get(id=staff_id)
                user = CustomUser.objects.get(id=staff.admin.id)
                user.username = username
                user.email = email
                if password != None:
                    user.admin.password = password
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    staff.profile_pic = passport_url
                user.first_name = first_name
                user.last_name = last_name
                staff.gender = gender
                staff.address = address
                staff.course = course
                user.save()
                staff.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_staff', args=[staff_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
                return render(request, "hod_template/edit_staff_template.html", context)
        else:
            messages.error(request, "Please fil form properly")
            return render(request, "hod_template/edit_staff_template.html", context)
    else:
        user = CustomUser.objects.get(id=staff_id)
        staff = Staff.objects.get(id=user.id)
        return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    instance = get_object_or_404(Student, id=student_id)
    form = StudentForm(request.POST or None, instance=instance)
    context = {
        'form': form
    }
    if request.method == 'POST':
        if form.is_valid():
            first_name = form.cleaned_data.get('first_name')
            last_name = form.cleaned_data.get('last_name')
            address = form.cleaned_data.get('address')
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            gender = form.cleaned_data.get('gender')
            password = form.cleaned_data.get('password') or None
            course = form.cleaned_data.get('course')
            session = form.cleaned_data.get('session')
            passport = request.FILES.get('profile_pic') or None
            try:
                student = Student.objects.get(id=student_id)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    student.profile_pic = passport_url
                user = CustomUser.objects.get(id=student.admin.id)
                user.username = username
                user.email = email
                if password != None:
                    user.admin.password = password
                user.first_name = first_name
                user.last_name = last_name
                student.session = session
                student.gender = gender
                student.address = address
                student.course = course
                user.save()
                student.save()
                messages.success(request, "Successfully Updated")
                return redirect(reverse('edit_student', args=[student_id]))
            except Exception as e:
                messages.error(request, "Could Not Update " + str(e))
                return render(request, "hod_template/edit_student_template.html", context)
        else:
            messages.error(request, "Please Fill Form Properly!")
            return render(request, "hod_template/edit_student_template.html", context)

    else:
        return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    instance = get_object_or_404(Course, id=course_id)
    form = CourseForm(request.POST or None, instance=instance)
    context = {
        'form': form
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            try:
                course = Course.objects.get(id=course_id)
                course.name = name
                course.save()
                messages.success(request, "Successfully Updated")
                return render(request, 'hod_template/edit_course_template.html', context)
            except:
                messages.error(request, "Could Not Update")
                return render(request, 'hod_template/edit_course_template.html', context)
        else:
            messages.error(request, "Could Not Update")
            return render(request, 'hod_template/edit_course_template.html', context)

    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    instance = get_object_or_404(Subject, id=subject_id)
    form = SubjectForm(request.POST or None, instance=instance)
    context = {
        'form': form
    }
    if request.method == 'POST':
        if form.is_valid():
            name = form.cleaned_data.get('name')
            course = form.cleaned_data.get('course')
            staff = form.cleaned_data.get('staff')
            try:
                subject = Subject.objects.get(id=subject_id)
                subject.name = name
                subject.staff = staff
                subject.course = course
                subject.save()
                messages.success(request, "Successfully Added")
                return redirect(reverse('edit_subject', args=[subject_id]))
            except Exception as e:
                messages.error(request, "Could Not Add " + str(e))
                return render(request, 'hod_template/edit_subject_template.html', context)

        else:
            messages.error(request, "Fill Form Properly")
            return render(request, 'hod_template/edit_subject_template.html', context)
    return render(request, 'hod_template/edit_subject_template.html', context)


def add_session(request):
    form = SessionForm(request.POST or None)
    context = {'form': form}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Created")
                return redirect(reverse('add_session'))
            except Exception as e:
                messages.error(request, 'Could Not Add ' + str(e))
                return render(request, "hod_template/add_session_template.html", context)
        else:
            messages.error(request, 'Fill Form Properly ')
            return render(request, "hod_template/add_session_template.html", context)
    else:
        return render(request, "hod_template/add_session_template.html", context)


def manage_session(request):
    sessions = Session.objects.all()
    context = {'sessions': sessions}
    return render(request, "hod_template/manage_session.html", context)


def edit_session(request, session_id):
    instance = get_object_or_404(Session, id=session_id)
    form = SessionForm(request.POST or None, instance=instance)
    context = {'form': form}
    if request.method == 'POST':
        if form.is_valid():
            try:
                form.save()
                messages.success(request, "Session Updated")
                return redirect(reverse('edit_session', args=[session_id]))
            except Exception as e:
                messages.error(
                    request, "Session Could Not Be Updated " + str(e))
                return render(request, "hod_template/edit_session_template.html", context)
        else:
            messages.error(request, "Invalid Form Submitted ")
            return render(request, "hod_template/edit_session_template.html", context)

    else:
        return render(request, "hod_template/edit_session_template.html", context)
