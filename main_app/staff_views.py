import json

from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.core.files.storage import FileSystemStorage
from django.db import transaction
from django.db.models import Count
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,redirect, render)
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from .forms import *
from .models import *

# Maximum scores accepted for a result (mirrors the limits used in the UI).
MAX_TEST_SCORE = 40
MAX_EXAM_SCORE = 60


def get_current_staff(request):
    """Return the Staff record of the logged in user, or deny access."""
    if not request.user.is_authenticated or request.user.user_type != '2':
        raise PermissionDenied
    return get_object_or_404(Staff, admin=request.user)


def get_staff_subject(staff, subject_id):
    """Return a subject only if it is taught by ``staff``."""
    return get_object_or_404(Subject, id=subject_id, staff=staff)


def parse_scores(test, exam):
    """Validate and convert test / exam scores, raising ValueError if invalid."""
    test = float(test)
    exam = float(exam)
    if not (0 <= test <= MAX_TEST_SCORE) or not (0 <= exam <= MAX_EXAM_SCORE):
        raise ValueError("Score out of range")
    return test, exam


def staff_home(request):
    staff = get_object_or_404(Staff.objects.select_related('admin', 'course'), admin=request.user)
    total_students = Student.objects.filter(course=staff.course).count()
    total_leave = LeaveReportStaff.objects.filter(staff=staff).count()
    # One query for the subjects together with their attendance counts
    subjects = list(Subject.objects.filter(staff=staff).annotate(
        attendance_count=Count('attendance')))
    total_subject = len(subjects)
    subject_list = [subject.name for subject in subjects]
    attendance_list = [subject.attendance_count for subject in subjects]
    total_attendance = sum(attendance_list)
    context = {
        'page_title': 'Staff Panel - ' + str(staff.admin.last_name) + ' (' + str(staff.course) + ')',
        'total_students': total_students,
        'total_attendance': total_attendance,
        'total_leave': total_leave,
        'total_subject': total_subject,
        'subject_list': subject_list,
        'attendance_list': attendance_list
    }
    return render(request, 'staff_template/home_content.html', context)


def staff_take_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Take Attendance'
    }

    return render(request, 'staff_template/staff_take_attendance.html', context)

@require_POST
def get_students(request):
    staff = get_current_staff(request)
    subject = get_staff_subject(staff, request.POST.get('subject'))
    session = get_object_or_404(Session, id=request.POST.get('session'))
    students = Student.objects.filter(
        course_id=subject.course_id, session=session).select_related('admin')
    student_data = []
    for student in students:
        data = {
                "id": student.id,
                "name": student.admin.last_name + " " + student.admin.first_name
                }
        student_data.append(data)
    return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)


@require_POST
def save_attendance(request):
    staff = get_current_staff(request)
    subject = get_staff_subject(staff, request.POST.get('subject'))
    session = get_object_or_404(Session, id=request.POST.get('session'))
    date = request.POST.get('date')
    try:
        students = json.loads(request.POST.get('student_ids') or '')
        if not isinstance(students, list):
            raise ValueError
        with transaction.atomic():
            # Check if an attendance object already exists for the given date and session
            attendance, created = Attendance.objects.get_or_create(session=session, subject=subject, date=date)

            for student_dict in students:
                # Only students offering this subject in this session can be marked
                student = Student.objects.get(
                    id=student_dict.get('id'), course=subject.course, session=session)

                # Check if an attendance report already exists for the student and the attendance object
                attendance_report, report_created = AttendanceReport.objects.get_or_create(student=student, attendance=attendance)

                # Update the status only if the attendance report was newly created
                if report_created:
                    attendance_report.status = bool(int(student_dict.get('status')))
                    attendance_report.save()
    except Exception:
        return HttpResponseBadRequest("Invalid attendance data")

    return HttpResponse("OK")


def staff_update_attendance(request):
    staff = get_object_or_404(Staff, admin=request.user)
    subjects = Subject.objects.filter(staff_id=staff)
    sessions = Session.objects.all()
    context = {
        'subjects': subjects,
        'sessions': sessions,
        'page_title': 'Update Attendance'
    }

    return render(request, 'staff_template/staff_update_attendance.html', context)


@require_POST
def get_student_attendance(request):
    staff = get_current_staff(request)
    attendance = get_object_or_404(
        Attendance, id=request.POST.get('attendance_date_id'), subject__staff=staff)
    attendance_data = AttendanceReport.objects.filter(
        attendance=attendance).select_related('student__admin')
    student_data = []
    for report in attendance_data:
        data = {"id": report.student.admin.id,
                "name": report.student.admin.last_name + " " + report.student.admin.first_name,
                "status": report.status}
        student_data.append(data)
    return JsonResponse(json.dumps(student_data), content_type='application/json', safe=False)


@require_POST
def update_attendance(request):
    staff = get_current_staff(request)
    attendance = get_object_or_404(
        Attendance, id=request.POST.get('date'), subject__staff=staff)
    try:
        students = json.loads(request.POST.get('student_ids') or '')
        if not isinstance(students, list):
            raise ValueError
        with transaction.atomic():
            for student_dict in students:
                # Only reports belonging to this attendance can be changed
                attendance_report = AttendanceReport.objects.get(
                    student__admin_id=student_dict.get('id'), attendance=attendance)
                attendance_report.status = bool(int(student_dict.get('status')))
                attendance_report.save()
    except Exception:
        return HttpResponseBadRequest("Invalid attendance data")

    return HttpResponse("OK")


def staff_apply_leave(request):
    form = LeaveReportStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'leave_history': LeaveReportStaff.objects.filter(staff=staff),
        'page_title': 'Apply for Leave'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(
                    request, "Application for leave has been submitted for review")
                return redirect(reverse('staff_apply_leave'))
            except Exception:
                messages.error(request, "Could not apply!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_apply_leave.html", context)


def staff_feedback(request):
    form = FeedbackStaffForm(request.POST or None)
    staff = get_object_or_404(Staff, admin_id=request.user.id)
    context = {
        'form': form,
        'feedbacks': FeedbackStaff.objects.filter(staff=staff),
        'page_title': 'Add Feedback'
    }
    if request.method == 'POST':
        if form.is_valid():
            try:
                obj = form.save(commit=False)
                obj.staff = staff
                obj.save()
                messages.success(request, "Feedback submitted for review")
                return redirect(reverse('staff_feedback'))
            except Exception:
                messages.error(request, "Could not Submit!")
        else:
            messages.error(request, "Form has errors!")
    return render(request, "staff_template/staff_feedback.html", context)


def staff_view_profile(request):
    staff = get_object_or_404(Staff, admin=request.user)
    form = StaffEditForm(request.POST or None, request.FILES or None,instance=staff)
    context = {'form': form, 'page_title': 'View/Update Profile'}
    if request.method == 'POST':
        try:
            if form.is_valid():
                first_name = form.cleaned_data.get('first_name')
                last_name = form.cleaned_data.get('last_name')
                password = form.cleaned_data.get('password') or None
                address = form.cleaned_data.get('address')
                gender = form.cleaned_data.get('gender')
                passport = request.FILES.get('profile_pic') or None
                admin = staff.admin
                if password != None:
                    admin.set_password(password)
                if passport != None:
                    fs = FileSystemStorage()
                    filename = fs.save(passport.name, passport)
                    passport_url = fs.url(filename)
                    admin.profile_pic = passport_url
                admin.first_name = first_name
                admin.last_name = last_name
                admin.address = address
                admin.gender = gender
                admin.save()
                staff.save()
                messages.success(request, "Profile Updated!")
                return redirect(reverse('staff_view_profile'))
            else:
                messages.error(request, "Invalid Data Provided")
                return render(request, "staff_template/staff_view_profile.html", context)
        except Exception as e:
            messages.error(
                request, "Error Occured While Updating Profile " + str(e))
            return render(request, "staff_template/staff_view_profile.html", context)

    return render(request, "staff_template/staff_view_profile.html", context)


def staff_fcmtoken(request):
    token = request.POST.get('token')
    try:
        staff_user = get_object_or_404(CustomUser, id=request.user.id)
        staff_user.fcm_token = token
        staff_user.save()
        return HttpResponse("True")
    except Exception as e:
        return HttpResponse("False")


def staff_view_notification(request):
    staff = get_object_or_404(Staff, admin=request.user)
    notifications = NotificationStaff.objects.filter(staff=staff)
    context = {
        'notifications': notifications,
        'page_title': "View Notifications"
    }
    return render(request, "staff_template/staff_view_notification.html", context)


def staff_add_result(request):
    staff = get_current_staff(request)
    subjects = Subject.objects.filter(staff=staff)
    sessions = Session.objects.all()
    context = {
        'page_title': 'Result Upload',
        'subjects': subjects,
        'sessions': sessions
    }
    if request.method == 'POST':
        try:
            student_id = request.POST.get('student_list')
            subject_id = request.POST.get('subject')
            test, exam = parse_scores(request.POST.get('test'), request.POST.get('exam'))
            # Only subjects taught by this staff, and students offering that subject
            subject = Subject.objects.get(id=subject_id, staff=staff)
            student = Student.objects.get(id=student_id, course=subject.course)
            data, created = StudentResult.objects.get_or_create(
                student=student, subject=subject, defaults={'test': test, 'exam': exam})
            if created:
                messages.success(request, "Scores Saved")
            else:
                data.exam = exam
                data.test = test
                data.save()
                messages.success(request, "Scores Updated")
        except Exception as e:
            messages.warning(request, "Error Occured While Processing Form")
    return render(request, "staff_template/staff_add_result.html", context)


@require_POST
def fetch_student_result(request):
    staff = get_current_staff(request)
    try:
        subject = Subject.objects.get(id=request.POST.get('subject'), staff=staff)
        student = Student.objects.get(id=request.POST.get('student'), course=subject.course)
        result = StudentResult.objects.get(student=student, subject=subject)
        result_data = {
            'exam': result.exam,
            'test': result.test
        }
        return HttpResponse(json.dumps(result_data))
    except Exception as e:
        return HttpResponse('False')


class EditResultView(View):
    """Lets a staff member edit results for subjects they teach only."""

    def dispatch(self, request, *args, **kwargs):
        self.staff = get_current_staff(request)
        return super().dispatch(request, *args, **kwargs)

    def get_form(self, data=None):
        form = EditResultForm(data)
        subjects = Subject.objects.filter(staff=self.staff)
        form.fields['subject'].queryset = subjects
        form.fields['student'].queryset = Student.objects.filter(
            course__in=subjects.values('course'))
        return form

    def get(self, request, *args, **kwargs):
        context = {
            'form': self.get_form(),
            'page_title': "Edit Student's Result"
        }
        return render(request, "staff_template/edit_student_result.html", context)

    def post(self, request, *args, **kwargs):
        form = self.get_form(request.POST)
        context = {'form': form, 'page_title': "Edit Student's Result"}
        if form.is_valid():
            try:
                student = form.cleaned_data.get('student')
                subject = form.cleaned_data.get('subject')
                test, exam = parse_scores(form.cleaned_data.get('test'), form.cleaned_data.get('exam'))
                # Validating: subject must be taught by this staff and the
                # student must offer the subject
                if subject.staff_id != self.staff.id or student.course_id != subject.course_id:
                    raise PermissionDenied
                result = StudentResult.objects.get(student=student, subject=subject)
                result.exam = exam
                result.test = test
                result.save()
                messages.success(request, "Result Updated")
                return redirect(reverse('edit_student_result'))
            except Exception as e:
                messages.warning(request, "Result Could Not Be Updated")
        else:
            messages.warning(request, "Result Could Not Be Updated")
        return render(request, "staff_template/edit_student_result.html", context)
