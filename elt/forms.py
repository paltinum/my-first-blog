from django import forms
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import ELTcores
from django.contrib import messages
from .models import Post, Comment

class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ('title', 'text',)
        
class CreateNewList(forms.Form):
	name = forms.CharField(label="Full Name", max_length=200)
	check = forms.BooleanField(required=False)
	
	def clean_name(self):
		if ELTcores.objects.filter(name=self.cleaned_data['name']).exists():
			raise forms.ValidationError("This code has already been used please contact support@platinumlanguage.com for additional information.")
		return self.cleaned_data['name']

class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ('text',)
