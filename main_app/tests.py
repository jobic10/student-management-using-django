import datetime
import json

from django.db import connection
from django.test import Client, TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse

from .models import (Attendance, AttendanceReport, Course, CustomUser,
                     Session, Staff, Student, StudentResult, Subject)


def CaptureQueries():
    return CaptureQueriesContext(connection)


def make_user(email, user_type):
    user = CustomUser.objects.create_user(
        email=email, password='Passw0rd!', user_type=user_type,
        first_name='First', last_name='Last', gender='M', address='addr')
    user.refresh_from_db()
    return user


class AuthorizationTests(TestCase):
    """Regression tests for broken access control on staff endpoints."""

    def setUp(self):
        self.session = Session.objects.create(
            start_year=datetime.date(2026, 1, 1), end_year=datetime.date(2026, 12, 31))
        self.course_a = Course.objects.create(name='CSE')
        self.course_b = Course.objects.create(name='ECE')

        self.teacher_a = make_user('staff.a@example.com', 2)
        self.teacher_b = make_user('staff.b@example.com', 2)
        self.staff_a = Staff.objects.get(admin=self.teacher_a)
        self.staff_b = Staff.objects.get(admin=self.teacher_b)
        self.subject_a = Subject.objects.create(
            name='CSE-101', staff=self.staff_a, course=self.course_a)
        self.subject_b = Subject.objects.create(
            name='ECE-201', staff=self.staff_b, course=self.course_b)

        self.student_user = make_user('stu.a@example.com', 3)
        self.student = Student.objects.get(admin=self.student_user)
        self.student.course = self.course_a
        self.student.session = self.session
        self.student.save()

        self.result = StudentResult.objects.create(
            student=self.student, subject=self.subject_a, test=10, exam=20)

    def login(self, user):
        self.client.force_login(user)

    # Issue: class-based view bypasses middleware
    def test_student_cannot_edit_results(self):
        self.login(self.student_user)
        response = self.client.post(reverse('edit_student_result'), {
            'session_year': self.session.id, 'subject': self.subject_a.id,
            'student': self.student.id, 'test': 39, 'exam': 59})
        self.assertNotEqual(response.status_code, 200)
        self.result.refresh_from_db()
        self.assertEqual((self.result.test, self.result.exam), (10, 20))

    def test_student_redirected_from_edit_result_page(self):
        self.login(self.student_user)
        response = self.client.get(reverse('edit_student_result'))
        self.assertRedirects(response, reverse('student_home'),
                             fetch_redirect_response=False)

    def test_other_teacher_cannot_edit_results(self):
        self.login(self.teacher_b)
        self.client.post(reverse('edit_student_result'), {
            'session_year': self.session.id, 'subject': self.subject_a.id,
            'student': self.student.id, 'test': 39, 'exam': 59})
        self.result.refresh_from_db()
        self.assertEqual((self.result.test, self.result.exam), (10, 20))

    def test_owning_teacher_can_edit_results(self):
        self.login(self.teacher_a)
        response = self.client.post(reverse('edit_student_result'), {
            'session_year': self.session.id, 'subject': self.subject_a.id,
            'student': self.student.id, 'test': 39, 'exam': 59})
        self.assertRedirects(response, reverse('edit_student_result'),
                             fetch_redirect_response=False)
        self.result.refresh_from_db()
        self.assertEqual((self.result.test, self.result.exam), (39, 59))

    # Issue: teacher can modify grades across subjects
    def test_other_teacher_cannot_add_result(self):
        self.login(self.teacher_b)
        self.client.post(reverse('staff_add_result'), {
            'student_list': self.student.id, 'subject': self.subject_a.id,
            'test': 37, 'exam': 38})
        self.result.refresh_from_db()
        self.assertEqual((self.result.test, self.result.exam), (10, 20))

    def test_other_teacher_cannot_create_result(self):
        self.result.delete()
        self.login(self.teacher_b)
        self.client.post(reverse('staff_add_result'), {
            'student_list': self.student.id, 'subject': self.subject_a.id,
            'test': 37, 'exam': 38})
        self.assertFalse(StudentResult.objects.exists())

    def test_owning_teacher_can_add_result(self):
        self.login(self.teacher_a)
        self.client.post(reverse('staff_add_result'), {
            'student_list': self.student.id, 'subject': self.subject_a.id,
            'test': 37, 'exam': 38})
        self.result.refresh_from_db()
        self.assertEqual((self.result.test, self.result.exam), (37, 38))

    def test_out_of_range_scores_rejected(self):
        self.login(self.teacher_a)
        self.client.post(reverse('staff_add_result'), {
            'student_list': self.student.id, 'subject': self.subject_a.id,
            'test': 1000, 'exam': -5})
        self.result.refresh_from_db()
        self.assertEqual((self.result.test, self.result.exam), (10, 20))

    def test_other_teacher_cannot_fetch_result(self):
        self.login(self.teacher_b)
        response = self.client.post(reverse('fetch_student_result'), {
            'subject': self.subject_a.id, 'student': self.student.id})
        self.assertEqual(response.content, b'False')

    # Issue: IDOR in attendance endpoints
    def test_other_teacher_cannot_list_students(self):
        self.login(self.teacher_b)
        response = self.client.post(reverse('get_students'), {
            'subject': self.subject_a.id, 'session': self.session.id})
        self.assertEqual(response.status_code, 404)

    def test_owning_teacher_can_list_students(self):
        self.login(self.teacher_a)
        response = self.client.post(reverse('get_students'), {
            'subject': self.subject_a.id, 'session': self.session.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(json.loads(json.loads(response.content))[0]['id'],
                         self.student.id)

    def test_other_teacher_cannot_save_attendance(self):
        self.login(self.teacher_b)
        response = self.client.post(reverse('save_attendance'), {
            'student_ids': json.dumps([{'id': self.student.id, 'status': 1}]),
            'date': '2026-10-25', 'subject': self.subject_a.id,
            'session': self.session.id})
        self.assertEqual(response.status_code, 404)
        self.assertFalse(Attendance.objects.exists())

    def test_teacher_cannot_mark_student_outside_subject(self):
        other = make_user('stu.b@example.com', 3)
        other_student = Student.objects.get(admin=other)
        other_student.course = self.course_b
        other_student.session = self.session
        other_student.save()
        self.login(self.teacher_a)
        response = self.client.post(reverse('save_attendance'), {
            'student_ids': json.dumps([{'id': other_student.id, 'status': 1}]),
            'date': '2026-10-25', 'subject': self.subject_a.id,
            'session': self.session.id})
        self.assertEqual(response.status_code, 400)
        self.assertFalse(AttendanceReport.objects.exists())
        self.assertFalse(Attendance.objects.exists())

    def test_owning_teacher_can_save_attendance(self):
        self.login(self.teacher_a)
        response = self.client.post(reverse('save_attendance'), {
            'student_ids': json.dumps([{'id': self.student.id, 'status': 1}]),
            'date': '2026-10-25', 'subject': self.subject_a.id,
            'session': self.session.id})
        self.assertEqual(response.content, b'OK')
        self.assertTrue(AttendanceReport.objects.get(student=self.student).status)

    def _attendance_for_a(self):
        attendance = Attendance.objects.create(
            session=self.session, subject=self.subject_a, date='2026-10-25')
        AttendanceReport.objects.create(
            student=self.student, attendance=attendance, status=True)
        return attendance

    def test_other_teacher_cannot_read_attendance(self):
        attendance = self._attendance_for_a()
        self.login(self.teacher_b)
        response = self.client.post(reverse('get_student_attendance'), {
            'attendance_date_id': attendance.id})
        self.assertEqual(response.status_code, 404)
        response = self.client.post(reverse('get_attendance'), {
            'subject': self.subject_a.id, 'session': self.session.id})
        self.assertEqual(response.status_code, 404)

    def test_student_cannot_list_attendance_dates(self):
        self._attendance_for_a()
        self.login(self.student_user)
        response = self.client.post(reverse('get_attendance'), {
            'subject': self.subject_a.id, 'session': self.session.id})
        self.assertEqual(response.status_code, 403)

    def test_update_attendance_route_reachable_and_scoped(self):
        attendance = self._attendance_for_a()
        self.assertNotEqual(reverse('update_attendance'),
                            reverse('staff_update_attendance'))
        payload = {'date': attendance.id, 'student_ids': json.dumps(
            [{'id': self.student_user.id, 'status': 0}])}

        self.login(self.teacher_b)
        response = self.client.post(reverse('update_attendance'), payload)
        self.assertEqual(response.status_code, 404)
        self.assertTrue(AttendanceReport.objects.get().status)

        self.login(self.teacher_a)
        response = self.client.post(reverse('update_attendance'), payload)
        self.assertEqual(response.content, b'OK')
        self.assertFalse(AttendanceReport.objects.get().status)

    def test_attendance_endpoints_require_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.teacher_a)
        response = client.post(reverse('save_attendance'), {
            'student_ids': json.dumps([{'id': self.student.id, 'status': 1}]),
            'date': '2026-10-25', 'subject': self.subject_a.id,
            'session': self.session.id})
        self.assertEqual(response.status_code, 403)
        self.assertFalse(Attendance.objects.exists())

    def test_hod_can_list_attendance_dates(self):
        self._attendance_for_a()
        hod = make_user('hod@example.com', 1)
        self.login(hod)
        response = self.client.post(reverse('get_attendance'), {
            'subject': self.subject_a.id, 'session': self.session.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(json.loads(json.loads(response.content))), 1)


class HodSecurityTests(TestCase):
    def setUp(self):
        self.hod = make_user('hod@example.com', 1)
        self.client.force_login(self.hod)
        self.course = Course.objects.create(name='CSE')

    def test_delete_requires_post(self):
        response = self.client.get(reverse('delete_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 405)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

        response = self.client.post(reverse('delete_course', args=[self.course.id]))
        self.assertRedirects(response, reverse('manage_course'),
                             fetch_redirect_response=False)
        self.assertFalse(Course.objects.filter(id=self.course.id).exists())

    def test_delete_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.hod)
        response = client.post(reverse('delete_course', args=[self.course.id]))
        self.assertEqual(response.status_code, 403)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_staff_cannot_reach_hod_views(self):
        teacher = make_user('staff@example.com', 2)
        self.client.force_login(teacher)
        response = self.client.post(reverse('delete_course', args=[self.course.id]))
        self.assertRedirects(response, reverse('staff_home'),
                             fetch_redirect_response=False)
        self.assertTrue(Course.objects.filter(id=self.course.id).exists())

    def test_anonymous_redirected_to_login(self):
        self.client.logout()
        response = self.client.get(reverse('manage_course'))
        self.assertRedirects(response, reverse('login_page'),
                             fetch_redirect_response=False)

    def test_notification_saved_without_fcm_key(self):
        student_user = make_user('stu@example.com', 3)
        with self.settings(FCM_SERVER_KEY=''):
            response = self.client.post(reverse('send_student_notification'), {
                'id': student_user.id, 'message': 'Hello'})
        self.assertEqual(response.content, b'True')
        self.assertEqual(Student.objects.get(admin=student_user)
                         .notificationstudent_set.get().message, 'Hello')

    def test_no_hardcoded_secrets_in_source(self):
        import pathlib
        app_dir = pathlib.Path(__file__).resolve().parent
        source = ''.join(p.read_text() for p in app_dir.glob('*.py')
                         if p.name != 'tests.py')
        self.assertNotIn('AAAA3Bm8j_M', source)
        self.assertNotIn('6LfswtgZAAAAABX9gbLqe', source)


class QueryCountTests(TestCase):
    """Dashboards and listings must not issue one query per row (N+1)."""

    def setUp(self):
        self.session = Session.objects.create(
            start_year=datetime.date(2026, 1, 1), end_year=datetime.date(2026, 12, 31))
        self.course = Course.objects.create(name='CSE')
        self.hod = make_user('hod@example.com', 1)
        self.teacher = make_user('staff@example.com', 2)
        self.staff = Staff.objects.get(admin=self.teacher)
        self.staff.course = self.course
        self.staff.save()
        self.student_user = make_user('stu@example.com', 3)
        self.student = Student.objects.get(admin=self.student_user)
        self.student.course = self.course
        self.student.session = self.session
        self.student.save()

    def add_rows(self, count):
        start = Subject.objects.count()
        for i in range(start, start + count):
            subject = Subject.objects.create(
                name='Subject %d' % i, staff=self.staff, course=self.course)
            attendance = Attendance.objects.create(
                session=self.session, subject=subject, date='2026-10-%02d' % (i + 1))
            AttendanceReport.objects.create(
                student=self.student, attendance=attendance, status=bool(i % 2))
            StudentResult.objects.create(
                student=self.student, subject=subject, test=10, exam=20)
            user = make_user('extra%d@example.com' % i, 3)
            extra = Student.objects.get(admin=user)
            extra.course = self.course
            extra.save()

    def assertConstantQueries(self, user, url_name):
        self.client.force_login(user)
        url = reverse(url_name)
        self.add_rows(1)
        with CaptureQueries() as small:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.add_rows(5)
        with CaptureQueries() as large:
            self.assertEqual(self.client.get(url).status_code, 200)
        self.assertEqual(len(small), len(large),
                         '%s query count grows with rows' % url_name)

    def test_admin_home(self):
        self.assertConstantQueries(self.hod, 'admin_home')

    def test_manage_student(self):
        self.assertConstantQueries(self.hod, 'manage_student')

    def test_manage_subject(self):
        self.assertConstantQueries(self.hod, 'manage_subject')

    def test_staff_home(self):
        self.assertConstantQueries(self.teacher, 'staff_home')

    def test_student_home(self):
        self.assertConstantQueries(self.student_user, 'student_home')

    def test_student_view_result(self):
        self.assertConstantQueries(self.student_user, 'student_view_result')

    def test_student_home_counts(self):
        self.add_rows(4)
        self.client.force_login(self.student_user)
        context = self.client.get(reverse('student_home')).context
        self.assertEqual(context['total_attendance'], 4)
        self.assertEqual(context['data_present'], [0, 1, 0, 1])
        self.assertEqual(context['data_absent'], [1, 0, 1, 0])
        self.assertEqual(context['percent_present'], 50)


class LogoutTests(TestCase):
    def setUp(self):
        self.user = make_user('stu@example.com', 3)
        self.client.force_login(self.user)

    def test_logout_requires_post(self):
        response = self.client.get(reverse('user_logout'))
        self.assertEqual(response.status_code, 405)
        self.assertIn('_auth_user_id', self.client.session)

    def test_logout_requires_csrf_token(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        response = client.post(reverse('user_logout'))
        self.assertEqual(response.status_code, 403)
        self.assertIn('_auth_user_id', client.session)

    def test_post_logs_out(self):
        response = self.client.post(reverse('user_logout'))
        self.assertRedirects(response, '/', fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)

    def test_logout_rendered_as_form(self):
        content = self.client.get(reverse('student_home')).content.decode()
        self.assertIn('action="%s"' % reverse('user_logout'), content)
        self.assertNotIn('href="%s"' % reverse('user_logout'), content)

    def test_unknown_role_is_logged_out(self):
        CustomUser.objects.filter(pk=self.user.pk).update(user_type='9')
        response = self.client.get(reverse('student_home'))
        self.assertRedirects(response, reverse('login_page'),
                             fetch_redirect_response=False)
        self.assertNotIn('_auth_user_id', self.client.session)
