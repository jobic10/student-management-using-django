from .models import *
from django import forms
from django.forms.widgets import DateInput


class StudentForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(StudentForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    class Meta:
        model = Student
        fields = ['course', 'gender', 'address', 'profile_pic',
                  'session_start_year', 'session_end_year']
        widgets = {
            'session_start_year': DateInput(attrs={'type': 'date'}),
            'session_end_year': DateInput(attrs={'type': 'date'}),
        }


class CustomUserForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(required=True)
    last_name = forms.CharField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    widget = {
        'password': forms.PasswordInput()
    }

    def __init__(self, *args, **kwargs):
        super(CustomUserForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs['class'] = 'form-control'

    def clean_email(self):
        if CustomUser.objects.filter(email=self.cleaned_data['email']).exists():
            raise forms.ValidationError("The email is already registered")
        return self.cleaned_data['email']

    class Meta:
        model = CustomUser
        fields = ('first_name', 'last_name', 'email', 'username', 'password', )
        help_texts = {'username': None}
