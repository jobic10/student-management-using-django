from django.contrib import messages
from django.core.files.storage import FileSystemStorage
from django.shortcuts import redirect, render

from .models import *


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
        passport = request.FILES.get('passport')
        fs = FileSystemStorage()
        filename = fs.save(passport.name, passport)
        passport_url = fs.url(filename)
        try:
            course = Course.objects.get(id=course_id)
            user = CustomUser.objects.create_user(
                username=username, email=email, password=password, user_type=2, first_name=first_name, last_name=last_name)
            user.staff.gender = gender
            user.staff.address = address
            user.staff.profile_pic = passport_url
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
        passport = request.FILES['passport']
        fs = FileSystemStorage()
        filename = fs.save(passport.name, passport)
        passport_url = fs.url(filename)
        try:
            course = Course.objects.get(id=course_id)

            user = CustomUser.objects.create_user(
                username=username, email=email, password=password, user_type=3, first_name=first_name, last_name=last_name)
            user.student.gender = gender
            user.student.address = address
            user.student.profile_pic = passport_url
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
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        username = request.POST.get('username')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        password = request.POST.get('password') or None
        course_id = request.POST.get('course')
        passport = request.FILES.get('passport') or None
        try:
            course = Course.objects.get(id=course_id)
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
            return redirect('/edit_staff/'+str(staff_id))
        except Exception as e:
            messages.warning(request, "Could Not Update " + str(e))
            return redirect('/edit_staff/'+str(staff_id))
    else:
        user = CustomUser.objects.get(id=staff_id)
        staff = Staff.objects.get(id=user.id)
        context = {
            "staff": staff,
            'courses': Course.objects.all(),
        }
        return render(request, "hod_template/edit_staff_template.html", context)


def edit_student(request, student_id):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        address = request.POST.get('address')
        username = request.POST.get('username')
        email = request.POST.get('email')
        gender = request.POST.get('gender')
        password = request.POST.get('password') or None
        course_id = request.POST.get('course')
        session_start = request.POST.get('session_start')
        session_end = request.POST.get('session_end')
        passport = request.FILES.get('passport') or None
        try:
            course = Course.objects.get(id=course_id)
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
            student.gender = gender
            student.address = address
            student.course = course
            user.save()
            student.save()
            messages.success(request, "Successfully Updated")
            return redirect('/edit_student/'+str(student_id))
        except Exception as e:
            messages.warning(request, "Could Not Update " + str(e))
            return redirect('/edit_student/'+str(student_id))
    else:
        student = Student.objects.get(id=student_id)
        context = {
            "student": student,
            'courses': Course.objects.all()
        }
        return render(request, "hod_template/edit_student_template.html", context)


def edit_course(request, course_id):
    if request.method == 'POST':
        name = request.POST.get('name')
        try:
            course = Course.objects.get(id=course_id)
            course.name = name
            course.save()
            messages.success(request, "Successfully Updated")
            return redirect('/edit_course/' + str(course_id))
        except:
            messages.warning(request, "Could Not Update")
            return redirect('/edit_course/' + str(course_id))
    context = {
        'course': Course.objects.get(id=course_id)
    }
    return render(request, 'hod_template/edit_course_template.html', context)


def edit_subject(request, subject_id):
    if request.method == 'POST':
        name = request.POST.get('name')
        course_id = request.POST.get('course')
        staff_id = request.POST.get('staff')
        print(f'I got back {course_id} and {staff_id} ')
        try:
            course = Course.objects.get(id=course_id)
            staff = CustomUser.objects.get(id=staff_id)
            subject = Subject.objects.get(id=subject_id)
            subject.name = name
            subject.staff = staff
            subject.course = course
            subject.save()
            print(f'I got back {course.name} and {staff.first_name} ')
            messages.success(request, "Successfully Added")
            return redirect('/edit_subject/' + str(subject_id))
        except Exception as e:
            messages.warning(request, "Could Not Add " + str(e))
            return redirect('/add_subject/' + str(subject_id))
    context = {
        'courses': Course.objects.all(),
        'staff': CustomUser.objects.filter(user_type=2),
        'subject': Subject.objects.get(id=subject_id)
    }
    return render(request, 'hod_template/edit_subject_template.html', context)
