from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Profile
class RegisterForm(UserCreationForm):
	email = forms.EmailField()
	first_name = forms.CharField()
	last_name = forms.CharField()

	def clean_email(self):
		if User.objects.filter(email=self.cleaned_data['email']).exists():
			raise forms.ValidationError("We are unable to register this email, please try again with a different one.")
		return self.cleaned_data['email']

	class Meta:
		model = User
		fields = ["first_name", "last_name", "username", "email", "password1", "password2"]

	def __str__(self):
		return self.email

class UserUpdateForm(forms.ModelForm):
	email = forms.EmailField()
	first_name = forms.CharField()
	last_name = forms.CharField()
	class Meta:
		model = User
		fields = ["first_name", "last_name", "username", "email"]

class ProfileUpdateForm(forms.ModelForm):
	class Meta:
		model = Profile
		fields = ['image']