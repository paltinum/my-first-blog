from django.shortcuts import render, redirect
from .forms import RegisterForm, UserUpdateForm, ProfileUpdateForm
from . import forms
from django.core.mail import send_mail
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from django.http import HttpResponse
from tablib import Dataset

from .resources import StudentResource
from .models import Profile, Student
# Create your views here.
def register(request):
	if request.method == "POST":
		form = RegisterForm(request.POST)
		if form.is_valid():
			form.save()			
			username = form.cleaned_data.get('username')
			messages.success(request, f'Your account has been created! Please login')
			return redirect("login")
	else:
		form = RegisterForm()
	return render(request, "register/register.html", {"form":form})

@login_required
def profile(request):
	if request.method == 'POST':
		u_form = UserUpdateForm(request.POST, instance=request.user)
		p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
		if u_form.is_valid() and p_form.is_valid():
			u_form.save()
			p_form.save()
			messages.success(request, f'Your account has been updated!')
			return redirect('profile')

	else:
		u_form = UserUpdateForm(instance=request.user)
		p_form = ProfileUpdateForm(instance=request.user.profile)		
	context = {
		'u_form': u_form,
		'p_form': p_form
	}
	return render(request, 'register/profile.html', context)







def export_data(request):
    if request.method == 'POST':
        file_format = request.POST['file-format']
        student_resource = StudentResource()
        dataset = student_resource.export()
        if file_format == 'CSV':
            response = HttpResponse(dataset.csv, content_type='text/csv')
            response['Content-Disposition'] = 'attachment; filename="exported_data.csv"'
            return response        
        elif file_format == 'JSON':
            response = HttpResponse(dataset.json, content_type='application/json')
            response['Content-Disposition'] = 'attachment; filename="exported_data.json"'
            return response
        elif file_format == 'XLS (Excel)':
            response = HttpResponse(dataset.xls, content_type='application/vnd.ms-excel')
            response['Content-Disposition'] = 'attachment; filename="exported_data.xls"'
            return response   

    return render(request, 'register/export.html')

def import_data(request, UserCreationForm):
    if request.method == 'POST':
        file_format = request.POST['file-format']
        student_resource = StudentResource()
        dataset = Dataset()
        new_student = request.FILES['importData']

        if file_format == 'CSV':
            imported_data = dataset.load(new_student.read().decode('utf-8'),format='csv')
            result = student_resource.import_data(dataset, dry_run=True)
            admin.site.register(User)
        elif file_format == 'JSON':
            imported_data = dataset.load(new_student.read().decode('utf-8'),format='json')
            result = student_resource.import_data(dataset, dry_run=True)
            admin.site.register(User)
        if not result.has_errors():
            student_resource.import_data(dataset, dry_run=False)
        
    return render(request, 'register/import.html')

