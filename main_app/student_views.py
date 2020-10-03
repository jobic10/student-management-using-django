from django.contrib import messages
from django.shortcuts import (HttpResponseRedirect, get_object_or_404,
                              redirect, render)
from django.urls import reverse

from .forms import *
from .models import *


def student_home(request):
    return render(request, 'student_template/home_content.html')
