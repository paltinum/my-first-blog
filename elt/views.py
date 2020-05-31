import os
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse, HttpResponseRedirect
from .models import ELTcores, Item, Snippet, Post, Comment
from .forms import CreateNewList, PostForm, CommentForm
from register.forms import RegisterForm
from django.contrib.auth.models import User, Group
from django.contrib import messages
from django.views.generic import (
	ListView,
	DetailView,
	CreateView,
	UpdateView,
	DeleteView,
)
import datetime
import time
import playsound
import random
import speech_recognition as sr
from gtts import gTTS
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
# Create your views here.
from django.template.loader import get_template, render_to_string
from .utils import render_to_pdf #created in step 4
from django.core.mail import EmailMessage
from django.conf import settings
from django.utils import timezone
from django.contrib.auth.decorators import login_required
global score
score = 0
global err
err = 0
def generate_pdf(response, *args, **kwargs):
	global TOEFL_ITP
	global TOEFL_IBT
	global CEFR
	global IELTs
	global ACTFL
	global TOEFL_ITPC
	global TOEFL_IBTC
	global CEFRC
	global IELTsC
	global ACTFLC
	global ACTFLc
	global IELTsc
	global CEFRc
	global TOEFLIBT
	global TOEFLITP
	name = response.user.get_full_name()
	data = {
	"TOEFL_ITP":TOEFL_ITP,
	"CEFR":CEFR,
	"TOEFL_IBT":TOEFL_IBT,
	"IELTs":IELTs,
	"ACTFL":ACTFL,
	"TOEFL_ITPC":TOEFL_ITPC,
	"CEFRC":CEFRC,
	"TOEFL_IBTC":TOEFL_IBTC,
	"IELTsC":IELTsC,
	"ACTFLC":ACTFLC,
	"name":name
    }
	pdf2 = render_to_pdf('test.html', data)
	return HttpResponse(pdf2, content_type='application/pdf')


def uname(response):
	un = RegisterForm.objects.get("name")
	print(un)


def post_detail(request, pk):
	global form
	form = CommentForm()
	is_liked = False
	post = get_object_or_404(Post, pk=pk)
	if request.method == "POST":
		is_liked = False
		form = CommentForm(request.POST)
		if form.is_valid():
			comment = form.save(commit=False)
			comment.post = post
			comment.author = request.user
			comment.save()
			return redirect('post_detail', pk=post.pk)
		else:
			form = CommentForm()
		if request.POST.get("like"):
			post.likes.add(request.user)
			is_liked = True
			post.dislikes.remove(request.user)
			if is_liked == True:
				messages.warning(request, f'You already liked this post!')
			if is_liked == False:
				is_liked = True
		if request.POST.get("dislike"):
			post.likes.remove(request.user)
			post.dislikes.add(request.user)
			if is_liked == False:
				messages.warning(request, f'You already disliked this post!')
			if is_liked == True:
				is_liked = False
	return render(request, 'main/post_detail.html', {'post': post, 'form':form, 'is_liked':is_liked})


@login_required
def post_new(request):
    if request.method == "POST":
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('post_detail', pk=post.pk)
    else:
        form = PostForm()
    return render(request, 'main/post_edit.html', {'form': form})

@login_required
def post_edit(request, pk):
    post = get_object_or_404(Post, pk=pk)
    if post.author == request.user:
	    if request.method == "POST":
	        form = PostForm(request.POST, instance=post)
	        if form.is_valid():
	            post = form.save(commit=False)
	            post.author = request.user
	            post.save()
	            return redirect('post_detail', pk=post.pk)
	        else:
	        	messages.warning(response, f'SOrry but this is not a valid response. Please try again.')
	    else:
	        form = PostForm(instance=post)
    else:
    	return HttpResponseRedirect("/Q&A/")
    return render(request, 'main/post_edit.html', {'form': form})

class PostListView(ListView, CommentForm):
    model = Post
    form = CommentForm()
    template_name = 'main/post_list.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    ordering = ['published_date']
    paginate_by = 5

    def get_queryset(self):
    	return Post.objects.filter(published_date__isnull=False).order_by('-published_date')


class UserPostListView(ListView):
    model = Post
    template_name = 'elt/user_posts.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        user = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=user, published_date__isnull=False).order_by('-published_date')

class UserPostDraftListView(ListView):
    model = Post
    template_name = 'elt/user_draft.html'  # <app>/<model>_<viewtype>.html
    context_object_name = 'posts'
    paginate_by = 5

    def get_queryset(self):
        draft = get_object_or_404(User, username=self.kwargs.get('username'))
        return Post.objects.filter(author=draft, published_date__isnull=True).order_by('-created_date')

@login_required
def post_draft_list(request, user):
	post = Post.objects.get(request.user)
	if post.author == request.user:
		posts = Post.objects.filter(published_date__isnull=True).order_by('-created_date')
		return render(request, 'main/post_draft_list.html', {'posts': posts})
	return render(request, 'main/post_draft_list.html', {})

@login_required
def post_publish(request, pk):
	post = get_object_or_404(Post, pk=pk)
	if post.author == request.user:
	    post.publish()
	    return redirect('post_detail', pk=pk)

@login_required
def post_remove(request, pk):
	post = get_object_or_404(Post, pk=pk)
	if post.author == request.user:
	    post.delete()
	    return redirect('post_list')
	return redirect('post_list')

@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)

@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    comment.delete()
    return redirect('post_detail', pk=comment.post.pk)

def home(response):
	return render(response, "main/home.html", {})

def homelog(response):
	return render(response, "main/homelog.html", {})

def about_us(response):
	return render(response, "main/about_us.html", {})

def view(response):
    return render(response, "main/view.html", {})

#create a test for a user
def ELT(response):
	global t
	t = ELTcores()
	if response.method == "POST":
		form = CreateNewList(response.POST)
		if form.is_valid():
			n = form.cleaned_data["name"]
			if n == f'{response.user.groups.values_list("name", flat=True).first()}{response.user}2020':
				t = ELTcores(name=n)
				t.save()
				response.user.scores.add(t)  # adds the to do list to the current logged in user
				return HttpResponseRedirect("/%i" %t.id)
			else:
				messages.warning(response, f'That is an incorrect ID. Please contact support@platinumlanguage.com to check your credentials')
		else:
			messages.warning(response, f"This code has already been used; please contact support@platinumlanguage.com for additional information.")			
	else:
		form = CreateNewList()
 	

	return render(response, "main/create.html", {"form":form})
#restricts each test to a user


def testid(response, id):


	ls = ELTcores.objects.get(id=id)

	if ls in response.user.scores.all():
		if response.method == "POST":
		    if response.POST.get("save"):
		    	print("Test")
		    	introduction(response, id)
		    	return HttpResponseRedirect("/%i" %id + "/Test")
		   
		return render(response, "main/list.html", {"ls":ls})
	return render(response, "main/home.html", {})


def introduction(response, id, *args, **kwargs):
	global score
	global err
	global TOEFL_ITP
	global TOEFL_IBT
	global CEFR
	global IELTs
	global ACTFL
	global TOEFL_ITPC
	global TOEFL_IBTC
	global CEFRC
	global IELTsC
	global ACTFLC
	global ACTFLc
	global IELTsc
	global CEFRc
	global TOEFLIBT
	global TOEFLITP
	messages.warning(response, f'After clicking on the play button please allow at least 10 seconds for the examenier to start speaking. Do not press the button again.')
	random_intro = random.choice(introductions)	
	if response.method == "POST":
		if response.POST.get("save"):
			speak(random_intro)
		if response.POST.get("PDF"):
			name = response.user.get_full_name()
			data = {
			"TOEFL_ITP":TOEFL_ITP,
			"CEFR":CEFR,
			"TOEFL_IBT":TOEFL_IBT,
			"IELTs":IELTs,
			"ACTFL":ACTFL,
			"TOEFL_ITPC":TOEFL_ITPC,
			"CEFRC":CEFRC,
			"TOEFL_IBTC":TOEFL_IBTC,
			"IELTsC":IELTsC,
			"ACTFLC":ACTFLC,
			"name":name
		    }
			email = response.user.email
			msg_html = render_to_string('email.html', data)
			msg = EmailMessage(name + f"'s Results", msg_html, "support@platinumlanguage.com", [email])
			msg.content_subtype = "html"  # Main content is now text/html
			msg.send()
			return HttpResponseRedirect("/results/")
		if response.POST.get("MIC"):
			if score > 0:
				messages.success(response, f'You just finished speaking! Press Play for the next question.')
			if score == 0:
				messages.warning(response, f'You have not heard the first question yet, please press Play to begin the test.')
			if score == 1:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if said in A1_1_A:
							good()
							score = score + 27
							print(score)
							print(said)
						else:
							aop()
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))					

			if score == 3:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if said in A1_2_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))							
			if score == 5:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)
						if said in A1_3_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))						
			if score == 7:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_4_A:
							good()
							score = score + 27
							print(score)
							print(said)
						else:
							aop()
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))							
			if score == 9:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_5_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))							
			if score == 11:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_6_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))					
			if score == 13:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_7_A:
							good()
							score = score + 27
							print(score)
							print(said)
						else:
							aop()
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 15:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_8_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 17:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_9_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 19:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_10_A:
							score = score + 27
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 21:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_11_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 23:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_12_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 25:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_13_A:
							score = score + 27
							print(score)
							print(said)
						else:
							score = score + 1
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 27:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A1_14_A:
							speak("You have finished the Test! Your CEFR level is A1")
							print(score)
							print(said)
							TOEFLITP = [
							"You need to continue your learning path of the English language since it is not enough to grant a level in the TOEFL certification.",
							"Platinum can increase your score at least 2 levels by taking a 6 month intensive course."
							]
							TOEFLIBT = [
							"Your English Level is currently being developed, We invite you to continue preparing yourself by taking a language course with us."
							]
							CEFRc = [
							"Can understand and use familiar everyday expressions and very basic phrases aimed at the satisfaction of needs of a concrete type. Can introduce him/herself and others and can ask and answer questions about personal details such as where he/she lives, people he/she knows and things he/she has. Can interact in a simple way provided the other person talks slowly and clearly and is prepared to help."
							]
							IELTsc = [
							"At this level, test-takers understand English only in its simplest, most common use. And even there, communication breaks down frequently.",
							"The test-taker can understand some small amount of English, but only with great difficulty."
							"The test taker knows only a few words and phrases in English.",
							]
							ACTFLc = [
							"Expresses self in conversations on very familiar topics using a variety of words, phrases, simple sentences, and questions that have been highly practiced and memorized.",
							"Can usually comprehend highly practiced and basic messages when supported by visual or contextual clues, redundancy or restatement, and when the message contains familiar structures."
							]
							TOEFL_ITP = "150<300"
							TOEFL_IBT = "10<25"
							CEFR = "A1"
							IELTs = "2<4"
							ACTFL = "Novice Low"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
						else:
							speak("You have finished the Test! Your CEFR level is A1")
							print(score)
							print(said)
							TOEFLITP = [
							"You need to continue your learning path of the English language since it is not enough to grant a level in the TOEFL certification.",
							"Platinum can increase your score at least 2 levels by taking a 6 month intensive course."
							]
							TOEFLIBT = [
							"Your English Level is currently being developed, We invite you to continue preparing yourself by taking a language course with us."
							]
							CEFRc = [
							"Can understand and use familiar everyday expressions and very basic phrases aimed at the satisfaction of needs of a concrete type. Can introduce him/herself and others and can ask and answer questions about personal details such as where he/she lives, people he/she knows and things he/she has. Can interact in a simple way provided the other person talks slowly and clearly and is prepared to help."
							]
							IELTsc = [
							"At this level, test-takers understand English only in its simplest, most common use. And even there, communication breaks down frequently.",
							"The test-taker can understand some small amount of English, but only with great difficulty."
							"The test taker knows only a few words and phrases in English.",
							]
							ACTFLc = [
							"Expresses self in conversations on very familiar topics using a variety of words, phrases, simple sentences, and questions that have been highly practiced and memorized.",
							"Can usually comprehend highly practiced and basic messages when supported by visual or contextual clues, redundancy or restatement, and when the message contains familiar structures."
							]
							TOEFL_ITP = "0<150"
							TOEFL_IBT = "0<10"
							CEFR = "A1"
							IELTs = "0<2"
							ACTFL = "Novice Low"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
					except sr.UnknownValueError:
						print("I'm sorry I couldn't understand.")
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						else:
							speak("You have finished the Test! Your CEFR level is A1")	
							TOEFLITP = [
							"You need to continue your learning path of the English language since it is not enough to grant a level in the TOEFL certification.",
							"Platinum can increase your score at least 2 levels by taking a 6 month intensive course."
							]
							TOEFLIBT = [
							"Your English Level is currently being developed, We invite you to continue preparing yourself by taking a language course with us."
							]
							CEFRc = [
							"Can understand and use familiar everyday expressions and very basic phrases aimed at the satisfaction of needs of a concrete type. Can introduce him/herself and others and can ask and answer questions about personal details such as where he/she lives, people he/she knows and things he/she has. Can interact in a simple way provided the other person talks slowly and clearly and is prepared to help."
							]
							IELTsc = [
							"At this level, test-takers understand English only in its simplest, most common use. And even there, communication breaks down frequently.",
							"The test-taker can understand some small amount of English, but only with great difficulty."
							"The test taker knows only a few words and phrases in English.",
							]
							ACTFLc = [
							"Expresses self in conversations on very familiar topics using a variety of words, phrases, simple sentences, and questions that have been highly practiced and memorized.",
							"Can usually comprehend highly practiced and basic messages when supported by visual or contextual clues, redundancy or restatement, and when the message contains familiar structures."
							]
							TOEFL_ITP = "0<150"
							TOEFL_IBT = "0<10"
							CEFR = "A1"
							IELTs = "0<2"
							ACTFL = "Novice Low"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})
					except sr.RequestError as e:
						print("Expetion:" + str(e))	
			if score == 29:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_1_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 27
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 31:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in A2_2_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 33:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_3_A:
							good()
							score = score + 23
							print(score)
							print(said)
						else:
							aop()
							score = score - 29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 35:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_4_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 27
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 37:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_5_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 39:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_6_A:
							good()
							score = score + 23
							print(score)
							print(said)
						else:
							aop()
							score = score -29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 41:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in A2_7_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 27
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 43:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in A2_8_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 45:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)
						if r.recognize_google(audio) in A2_9_A:
							score = score + 23
							print(score)
							print(said)
						else:
							score = score - 29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 47:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in A2_10_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 27
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 49:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in A2_11_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 51:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_12_A:
							score = score + 23
							print(score)
							print(said)
						else:
							score = score - 29
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 53:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_13_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 27
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 55:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in A2_14_A:
							speak("You have finished the Test! Your CEFR level is A2")
							print(score)
							print(said)
							TOEFLITP = [
							"Test takers at this level are sometimes able to: demonstrate familiarity with the most often used tenses of common verbs, use a singular or plural noun correctly as the subject of a sentence in very simple contexts, link subjects to nouns or adjectives with very common linking verbs, recognize that some common verbs require nouns as objects, make proper use of simple comparatives and common conjunctions and prepositions",
							"Test takers at this level are sometimes able, when listening to a short dialogue about an everyday situation, to: understand the main idea of the conversation, understand basic vocabulary, understand explicitly stated points that are reinforced or repeated, understand the antecedents for basic pronouns (e.g., 'it,' 'they,' 'yours')."
							]
							TOEFLIBT = [
							"Test takers who score at the Basic level typically can speak slowly and carefully so that they make themselves understood, but pronunciation may be strongly influenced by the speaker's first language and at times be unintelligible; speech may be marked by frequent pauses, reformulations, and false starts.",
							"Test takers who score at the Basic level typically can produce mostly short utterances, connecting phrases with simple linking words (such as 'and') to make themselves understood; grammar and vocabulary are limited, and frequent pauses may occur while searching for words."
							]
							CEFRc = [
							"Can understand sentences and frequently used expressions related to areas of most immediate relevance (e.g. very basic personal and family information, shopping, local geography, employment). Can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar and routine matters.  Can describe in simple terms aspects of his/her background, immediate environment and matters in areas of immediate need."
							]
							IELTsc = [
							"At this level, IELTS test-takers cannot use complex English language, and struggle to understand more complex English. Their English use is limited to simple, basic contexts."
							]
							ACTFLc = [
							"Comprehends some, but not all of the time, highly predictable vocabulary, a limited number of words related to familiar topics, and formulaic expressions.",
							"Produces words and phrases and highly practiced sentences or formulaic questions."
							]
							TOEFL_ITP = "330<450"
							TOEFL_IBT = "25<35"
							CEFR = "A2"
							IELTs = "3<4"
							ACTFL = "Novice Mid"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
						else:
							speak("You have finished the Test! Your CEFR level is A2")
							TOEFLITP = [
							"Test takers at this level are sometimes able to: demonstrate familiarity with the most often used tenses of common verbs, use a singular or plural noun correctly as the subject of a sentence in very simple contexts, link subjects to nouns or adjectives with very common linking verbs, recognize that some common verbs require nouns as objects, make proper use of simple comparatives and common conjunctions and prepositions",
							"Test takers at this level are sometimes able, when listening to a short dialogue about an everyday situation, to: understand the main idea of the conversation, understand basic vocabulary, understand explicitly stated points that are reinforced or repeated, understand the antecedents for basic pronouns (e.g., 'it,' 'they,' 'yours')."
							]
							TOEFLIBT = [
							"Test takers who score at the Basic level typically can speak slowly and carefully so that they make themselves understood, but pronunciation may be strongly influenced by the speaker's first language and at times be unintelligible; speech may be marked by frequent pauses, reformulations, and false starts.",
							"Test takers who score at the Basic level typically can produce mostly short utterances, connecting phrases with simple linking words (such as 'and') to make themselves understood; grammar and vocabulary are limited, and frequent pauses may occur while searching for words."
							]
							CEFRc = [
							"Can understand sentences and frequently used expressions related to areas of most immediate relevance (e.g. very basic personal and family information, shopping, local geography, employment). Can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar and routine matters.  Can describe in simple terms aspects of his/her background, immediate environment and matters in areas of immediate need."
							]
							IELTsc = [
							"At this level, IELTS test-takers cannot use complex English language, and struggle to understand more complex English. Their English use is limited to simple, basic contexts."
							]
							ACTFLc = [
							"Comprehends some, but not all of the time, highly predictable vocabulary, a limited number of words related to familiar topics, and formulaic expressions.",
							"Produces words and phrases and highly practiced sentences or formulaic questions."
							]
							TOEFL_ITP = "330<450"
							TOEFL_IBT = "25<35"
							CEFR = "A2"
							IELTs = "3<4"
							ACTFL = "Novice Mid"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
					except sr.UnknownValueError:
						print("Next question.")
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						else:
							speak("You have finished the Test! Your CEFR level is A1")	
							TOEFLITP = [
							"Test takers at this level are sometimes able to: demonstrate familiarity with the most often used tenses of common verbs, use a singular or plural noun correctly as the subject of a sentence in very simple contexts, link subjects to nouns or adjectives with very common linking verbs, recognize that some common verbs require nouns as objects, make proper use of simple comparatives and common conjunctions and prepositions",
							"Test takers at this level are sometimes able, when listening to a short dialogue about an everyday situation, to: understand the main idea of the conversation, understand basic vocabulary, understand explicitly stated points that are reinforced or repeated, understand the antecedents for basic pronouns (e.g., 'it,' 'they,' 'yours')."
							]
							TOEFLIBT = [
							"Test takers who score at the Basic level typically can speak slowly and carefully so that they make themselves understood, but pronunciation may be strongly influenced by the speaker's first language and at times be unintelligible; speech may be marked by frequent pauses, reformulations, and false starts.",
							"Test takers who score at the Basic level typically can produce mostly short utterances, connecting phrases with simple linking words (such as 'and') to make themselves understood; grammar and vocabulary are limited, and frequent pauses may occur while searching for words."
							]
							CEFRc = [
							"Can understand sentences and frequently used expressions related to areas of most immediate relevance (e.g. very basic personal and family information, shopping, local geography, employment). Can communicate in simple and routine tasks requiring a simple and direct exchange of information on familiar and routine matters.  Can describe in simple terms aspects of his/her background, immediate environment and matters in areas of immediate need."
							]
							IELTsc = [
							"At this level, IELTS test-takers cannot use complex English language, and struggle to understand more complex English. Their English use is limited to simple, basic contexts."
							]
							ACTFLc = [
							"Comprehends some, but not all of the time, highly predictable vocabulary, a limited number of words related to familiar topics, and formulaic expressions.",
							"Produces words and phrases and highly practiced sentences or formulaic questions."
							]
							TOEFL_ITP = "330<450"
							TOEFL_IBT = "25<35"
							CEFR = "A2"
							IELTs = "3<4"
							ACTFL = "Novice Mid"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})					
					except sr.RequestError as e:
						print("Expetion:" + str(e))

			if score == 57:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_1_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 23
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 59:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_2_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 25
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 61:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_3_A:
							score = score + 19
							print(score)
							print(said)
						else:
							aop()
							score = score - 25
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 63:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_4_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 23
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 65:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B1_5_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 25
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 67:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_6_A:
							score = score + 19
							print(score)
							print(said)
						else:
							score = score - 25
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 69:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_7_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 23
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 71:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio):
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 25
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 73:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_9_A:
							score = score + 19
							print(score)
							print(said)
						else:
							score = score - 25
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 75:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B1_10_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 23
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 77:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B1_11_A:
							score = score + 1
							print(score)
							print(said)
						else:
							print(score) - 25
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 79:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B1_12_A:
							speak("You have finished the Test! Your CEFR level is B1")
							print(score)
							print(said)
							TOEFLITP = [
							"Test takers at this level are usually able to: use common tenses of verbs correctly, including passive forms, use linking verbs with ease and use an expletive, such as 'there is' in the absence of another main verb, recognize when verbs require objects, such as infinitives, gerunds or clauses beginning with 'that', introduce a clause with very common words, such as 'before' or 'if', recognize the correct structure of a sentence or clause, even when its subject and verb are slightly separated",
							"Test takers at this level are usually able, when listening to a short dialogue, to: understand high-frequency vocabulary and deduce the meaning of some lower-frequency vocabulary, understand some commonly occurring idioms and colloquial expressions, understand implications (e.g., implied questions in the form of statements, indirect suggestions) that are clearly reinforced, understand common language functions (e.g., invitations, apologies, suggestions), recognize the referents for a variety of types of pronouns (e.g., 'their,' 'these,' 'one')."
							]
							TOEFLIBT = [
							"Test takers who score at the Low-Intermediate level typically can speak clearly with minor hesitancies about general or familiar topics; longer pauses are noticeable when speaking about more complex or academic topics, and mispronunciations may obscure meaning at times.",
							"Test takers who score at the Low-Intermediate level typically can produce short stretches of speech consisting of basic grammatical structures connected with 'and', 'because' and 'so'; attempts at longer utterances requiring more complex grammatical structures may be marked by errors and pauses for grammatical planning or repair; use vocabulary that is sufficient to discuss general or familiar topics, but limitations in range of vocabulary sometimes result in vague or unclear expression of ideas",
							"Test takers who score at the Low-Intermediate level typically can convey some main points and other relevant information but summaries, explanations, and opinions are sometimes incomplete, inaccurate, and/or lack detail; long or complex explanations may lack coherence."
							]
							CEFRc = [
							"Can understand the main points of clear standard input on familiar matters regularly encountered in work, school, leisure, etc. Can deal with most situations likely to arise whilst travelling in an area where the language is spoken.  Can produce simple connected text on topics which are familiar or of personal interest. Can describe experiences and events, dreams, hopes & ambitions and briefly give reasons and explanations for opinions and plans."
							]
							IELTsc = [
							"The English user has a 'partial command' of English, to quote the official band guide linked above this table. Such test-takers can 'get by' in English, having basic conversations with some strain, but are limited to English use only in simple contexts, or specialized contexts in their own field of expertise."
							]
							ACTFLc = [
							"Produces vocabulary on variety of everyday topics, topics of personal interest, and topics that have been studied.",
							"Communicates information and expresses own thoughts about familiar topics using sentences and series of sentences."
							]
							TOEFL_ITP = "460<540"
							TOEFL_IBT = "35<45"
							CEFR = "B1"
							IELTs = "4<5"
							ACTFL = "Intermediate mid"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
						else:
							speak("You have finished the Test! Your CEFR level is B1")
							print(score)
							print(said)
							TOEFLITP = [
							"Test takers at this level are usually able to: use common tenses of verbs correctly, including passive forms, use linking verbs with ease and use an expletive, such as 'there is' in the absence of another main verb, recognize when verbs require objects, such as infinitives, gerunds or clauses beginning with 'that', introduce a clause with very common words, such as 'before' or 'if', recognize the correct structure of a sentence or clause, even when its subject and verb are slightly separated",
							"Test takers at this level are usually able, when listening to a short dialogue, to: understand high-frequency vocabulary and deduce the meaning of some lower-frequency vocabulary, understand some commonly occurring idioms and colloquial expressions, understand implications (e.g., implied questions in the form of statements, indirect suggestions) that are clearly reinforced, understand common language functions (e.g., invitations, apologies, suggestions), recognize the referents for a variety of types of pronouns (e.g., 'their,' 'these,' 'one')."
							]
							TOEFLIBT = [
							"Test takers who score at the Low-Intermediate level typically can speak clearly with minor hesitancies about general or familiar topics; longer pauses are noticeable when speaking about more complex or academic topics, and mispronunciations may obscure meaning at times.",
							"Test takers who score at the Low-Intermediate level typically can produce short stretches of speech consisting of basic grammatical structures connected with 'and', 'because' and 'so'; attempts at longer utterances requiring more complex grammatical structures may be marked by errors and pauses for grammatical planning or repair; use vocabulary that is sufficient to discuss general or familiar topics, but limitations in range of vocabulary sometimes result in vague or unclear expression of ideas",
							"Test takers who score at the Low-Intermediate level typically can convey some main points and other relevant information but summaries, explanations, and opinions are sometimes incomplete, inaccurate, and/or lack detail; long or complex explanations may lack coherence."
							]
							CEFRc = [
							"Can understand the main points of clear standard input on familiar matters regularly encountered in work, school, leisure, etc. Can deal with most situations likely to arise whilst travelling in an area where the language is spoken.  Can produce simple connected text on topics which are familiar or of personal interest. Can describe experiences and events, dreams, hopes & ambitions and briefly give reasons and explanations for opinions and plans."
							]
							IELTsc = [
							"The English user has a 'partial command' of English, to quote the official band guide linked above this table. Such test-takers can 'get by' in English, having basic conversations with some strain, but are limited to English use only in simple contexts, or specialized contexts in their own field of expertise."
							]
							ACTFLc = [
							"Produces vocabulary on variety of everyday topics, topics of personal interest, and topics that have been studied.",
							"Communicates information and expresses own thoughts about familiar topics using sentences and series of sentences."
							]
							TOEFL_ITP = "460<540"
							TOEFL_IBT = "35<45"
							CEFR = "B1"
							IELTs = "4<5"
							ACTFL = "Intermediate mid"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})
					except sr.UnknownValueError:
						print("Next question.")
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						else:	
							speak("You have finished the Test! Your CEFR level is B1")
							TOEFLITP = [
							"Test takers at this level are usually able to: use common tenses of verbs correctly, including passive forms, use linking verbs with ease and use an expletive, such as 'there is' in the absence of another main verb, recognize when verbs require objects, such as infinitives, gerunds or clauses beginning with 'that', introduce a clause with very common words, such as 'before' or 'if', recognize the correct structure of a sentence or clause, even when its subject and verb are slightly separated",
							"Test takers at this level are usually able, when listening to a short dialogue, to: understand high-frequency vocabulary and deduce the meaning of some lower-frequency vocabulary, understand some commonly occurring idioms and colloquial expressions, understand implications (e.g., implied questions in the form of statements, indirect suggestions) that are clearly reinforced, understand common language functions (e.g., invitations, apologies, suggestions), recognize the referents for a variety of types of pronouns (e.g., 'their,' 'these,' 'one')."
							]
							TOEFLIBT = [
							"Test takers who score at the Low-Intermediate level typically can speak clearly with minor hesitancies about general or familiar topics; longer pauses are noticeable when speaking about more complex or academic topics, and mispronunciations may obscure meaning at times.",
							"Test takers who score at the Low-Intermediate level typically can produce short stretches of speech consisting of basic grammatical structures connected with 'and', 'because' and 'so'; attempts at longer utterances requiring more complex grammatical structures may be marked by errors and pauses for grammatical planning or repair; use vocabulary that is sufficient to discuss general or familiar topics, but limitations in range of vocabulary sometimes result in vague or unclear expression of ideas",
							"Test takers who score at the Low-Intermediate level typically can convey some main points and other relevant information but summaries, explanations, and opinions are sometimes incomplete, inaccurate, and/or lack detail; long or complex explanations may lack coherence."
							]
							CEFRc = [
							"Can understand the main points of clear standard input on familiar matters regularly encountered in work, school, leisure, etc. Can deal with most situations likely to arise whilst travelling in an area where the language is spoken.  Can produce simple connected text on topics which are familiar or of personal interest. Can describe experiences and events, dreams, hopes & ambitions and briefly give reasons and explanations for opinions and plans."
							]
							IELTsc = [
							"The English user has a 'partial command' of English, to quote the official band guide linked above this table. Such test-takers can 'get by' in English, having basic conversations with some strain, but are limited to English use only in simple contexts, or specialized contexts in their own field of expertise."
							]
							ACTFLc = [
							"Produces vocabulary on variety of everyday topics, topics of personal interest, and topics that have been studied.",
							"Communicates information and expresses own thoughts about familiar topics using sentences and series of sentences."
							]
							TOEFL_ITP = "460<540"
							TOEFL_IBT = "35<45"
							CEFR = "B1"
							IELTs = "4<5"
							ACTFL = "Intermediate mid"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 81:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio):
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 19
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 83:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B2_2_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 21
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 85:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B2_3_A:
							score = score + 15
							print(score)
							print(said)
						else:
							score = score - 21
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 87:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B2_4_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 19
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 89:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B2_5_A:
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 21
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 91:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in B2_6_A:
							good()
							score = score + 15
							print(score)
							print(said)
						else:
							aop()
							score = score - 21
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 93:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B2_7_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 19
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 95:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B2_8_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 21
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 97:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B2_9_A:
							score = score + 15
							print(score)
							print(said)
						else:
							print(score) + 1
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 99:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in B2_10_A:
							speak("You have finished the Test! Your CEFR level is B2")
							print(score)
							print(said)
							TOEFLITP = [
							"Test takers at this level are usually able, when listening to a short dialogue, to: integrate information across two utterances in order to understand an implied meaning, understand the meaning of a variety of idioms and colloquial expressions (e.g., 'It's probably for the best,' 'All I can say is ...')",
							"Test takers at this level are usually able to: use suffixes and other morphemes in crafting appropriate word forms, modify nouns by adding participles, relative clauses, appositives, etc. Deal with multiple and less frequent uses of common words, understand limitations imposed by the use of specific vocabulary, as with phrasal verbs such as “refer to” in which only a particular preposition may follow a particular verb, recognize acceptable variations in basic grammatical rules, as well as exceptions to those rules"
							]
							TOEFLIBT = [
							"Test takers who score at the High-Intermediate level typically can speak clearly and without hesitancy on general or familiar topics, with overall good intelligibility; pauses and hesitations (to recall or plan information) are sometimes noticeable when more demanding content is produced, and any mispronunciations or intonation errors only occasionally cause problems for the listener",
							"Test takers who score at the High-Intermediate level typically can produce stretches of speech that demonstrate control of some complex structures and a range of vocabulary, although occasional lapses in precision and accuracy may obscure meaning at times.",
							"Test takers who score at the High-Intermediate level typically can convey sufficient information to produce mostly complete summaries, explanations, and opinions, but some ideas may not be fully developed or may lack elaboration; any lapses in completeness and cohesion may at times affect the otherwise clear progression of ideas."
							]
							CEFRc = [
							"Can understand the main ideas of complex text on both concrete and abstract topics, including technical discussions in his/her field of specialisation. Can interact with a degree of fluency and spontaneity that makes regular interaction with native speakers quite possible without strain for either party. Can produce clear, detailed text on a wide range of subjects and explain a viewpoint on a topical issue giving the advantages and disadvantages of various options."
							]
							IELTsc = [
							"In this case, the test-taker is still strong in English, but performs the best in familiar situations, while facing difficulties with English in less-familiar or more specialized contexts."
							]
							ACTFLc = [
							"Expresses own thoughts and presents information and personal preferences on familiar topics by creating with language primarily in present time and creates messages in contexts relevant to oneself and others, and one’s immediate environment",
							"Control of language is sufficient to be understood by audiences accustomed to language produced by language learners. With practice, polish, or editing, may show emerging evidence of Advanced-level language control."
							]
							TOEFL_ITP = "550<610"
							TOEFL_IBT = "45<65"
							CEFR = "B2"
							IELTs = "5<6.5"
							ACTFL = "Advanced Mid"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
						else:
							aop()
							score = score - 21
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						else:
							aop()
							score = score - 21
					except sr.RequestError as e:
						print("Expetion:" + str(e))

			if score == 101:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in C1_1_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 15
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 103:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in C1_2_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 17
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 105:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in C1_3_A:
							score = score + 11
							print(score)
							print(said)
						else:
							score = score - 17
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 107:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in C1_4_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 15
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 109:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in C1_5_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 17
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 111:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in C1_6_A:
							score = score + 11
							print(score)
							print(said)
						else:
							aop()
							score = score - 17
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 113:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio):
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 15
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 115:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in C1_8_A:
							speak("You have finished the Test! Your CEFR level is C1")
							print(score)
							print(said)
							TOEFLITP = [
							"Test takers at this level are usually able to: Understand less familiar verb tenses, subjunctive mood and reduced clauses, such as 'while eating' and 'how to go'. Monitor interactions among various elements in a complex sentence for completeness of sentence structure, singular/plural agreement, etc. Deal with idioms and multiple usages of words, such as 'so' and 'as'. Recognize different levels of abstraction or formality in choices, such as 'in an agreement'/'in agreement', and 'The star was just discovered recently'/'Only recently was the star discovered'.",
							"Test takers at this level are usually able to: Understand the main idea or purpose of a short academic lecture or extended conversation that requires integrating or synthesizing information, recall important details presented in a discussion of academic material, understand complex time references and temporal relationships in a short dialogue, short academic lecture or extended conversation, understand some difficult and abstract vocabulary, follow the essential ideas in an extended conversation or academic lecture, even if some information is not fully understood."
							]
							TOEFLIBT = [
							"Test takers who score at the Advanced level typically can speak clearly and use intonation to support meaning so that speech is generally easy to understand and follow; any minor lapses do not obscure meaning.",
							"Test takers who score at the Advanced level typically can speak with relative ease on a range of general and academic topics, demonstrating control of an appropriate range of grammatical structures and vocabulary; any minor errors may be noticeable, but do not obscure meaning.",
							"Test takers who score at the Advanced level typically can convey mostly well-supported summaries, explanations, and opinions, including both concrete and abstract information, with generally well-controlled organization and cohesion; lapses may occur, but they rarely impact overall comprehensibility."
							]
							CEFRc = [
							"Can understand a wide range of demanding, longer texts, and recognise implicit meaning. Can express him/herself fluently and spontaneously without much obvious searching for expressions. Can use language flexibly and effectively for social, academic and professional purposes. Can produce clear, well-structured, detailed text on complex subjects, showing controlled use of organisational patterns, connectors and cohesive devices."
							]
							IELTsc = [
							"Skilled English user, but not native-like per se. Test-takers at this level are good with complex English use in general, but may make certain repeat errors, or be more limited in English in certain contexts."
							]
							ACTFLc = [
							"Uses cultural knowledge appropriate to the presentational context and increasingly reflective of authentic cultural practices and perspectives.",
							"Sufficient control of language (vocabulary, structures, conventions of spoken and written language, etc.) to understand fully and with ease more complex and descriptive texts with connected language and cohesive devices."
							]
							TOEFL_ITP = "620<640"
							TOEFL_IBT = "65<100"
							CEFR = "C1"
							IELTs = "6.5<8"
							ACTFL = "Superior"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
						else:
							aop()
							score = score - 17
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						else:
							speak("You have finished the Test! Your CEFR level is B2")
							score = score - 17
					except sr.RequestError as e:
						print("Expetion:" + str(e))

			if score == 117:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio):
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 11
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 119:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio):
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 13
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 121:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in C2_3_A:
							good()
							score = score + 1
							print(score)
							print(said)
						else:
							aop()
							score = score - 13
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 123:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)	
						if r.recognize_google(audio) in C2_4_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 11
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 125:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)		
						if r.recognize_google(audio) in C2_5_A:
							score = score + 1
							print(score)
							print(said)
						else:
							score = score - 13
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						score = score + 1
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						if err == 4:	
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 1 more time during the test, I will need you to retake the test with a different microphone source.")
						if err == 3:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 2 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 2:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 3 more times during the test, I will need you to retake the test with a different microphone source.")
						if err == 1:
							speak("I'm very sorry, but, I did not understand what you said, please speak clearer next time. If this happens 4 more times during the test, I will need you to retake the test with a different microphone source.")
					except sr.RequestError as e:
						print("Expetion:" + str(e))
			if score == 127:
				r = sr.Recognizer()
				with sr.Microphone() as source:
					audio = r.listen(source)
					said = ""
					try:
						said = r.recognize_google(audio)
						if r.recognize_google(audio) in C2_6_A:
							speak("You have finished the Test! Your CEFR level is C2")
							print(score)
							print(said)
							TOEFLITP = [
							"Test takers at this level are usually able to: Understand less familiar verb tenses, subjunctive mood and reduced clauses, such as 'while eating' and 'how to go'. Monitor interactions among various elements in a complex sentence for completeness of sentence structure, singular/plural agreement, etc. Deal with idioms and multiple usages of words, such as 'so' and 'as'. Recognize different levels of abstraction or formality in choices, such as 'in an agreement'/'in agreement', and 'The star was just discovered recently'/'Only recently was the star discovered'.",
							"Test takers at this level are usually able to: Understand the main idea or purpose of a short academic lecture or extended conversation that requires integrating or synthesizing information, recall important details presented in a discussion of academic material, understand complex time references and temporal relationships in a short dialogue, short academic lecture or extended conversation, understand some difficult and abstract vocabulary, follow the essential ideas in an extended conversation or academic lecture, even if some information is not fully understood."
							]
							TOEFLIBT = [
							"Test takers who score at the Advanced level typically can speak clearly and use intonation to support meaning so that speech is generally easy to understand and follow; any minor lapses do not obscure meaning.",
							"Test takers who score at the Advanced level typically can speak with relative ease on a range of general and academic topics, demonstrating control of an appropriate range of grammatical structures and vocabulary; any minor errors may be noticeable, but do not obscure meaning.",
							"Test takers who score at the Advanced level typically can convey mostly well-supported summaries, explanations, and opinions, including both concrete and abstract information, with generally well-controlled organization and cohesion; lapses may occur, but they rarely impact overall comprehensibility."
							]
							CEFRc = [
							"Can understand with ease virtually everything heard or read. Can summarise information from different spoken and written sources, reconstructing arguments and accounts in a coherent presentation. Can express him/herself spontaneously, very fluently and precisely, differentiating finer shades of meaning even in more complex situations."
							]
							IELTsc = [
							"Near-native/native fluency, with only occasional or no inaccuracies, mistakes, or misunderstandings."
							]
							ACTFLc = [
							"Uses cultural knowledge appropriate to the presentational context and increasingly reflective of authentic cultural practices and perspectives.",
							"Sufficient control of language (vocabulary, structures, conventions of spoken and written language, etc.) to understand fully and with ease more complex and descriptive texts with connected language and cohesive devices."
							]
							TOEFL_ITP = "635<"
							TOEFL_IBT = "110<"
							CEFR = "C2"
							IELTs = "8<9"
							ACTFL = "Distinguished"
							TOEFL_ITPC = random.choice(TOEFLITP)
							TOEFL_IBTC = random.choice(TOEFLIBT)
							CEFRC = random.choice(CEFRc)
							IELTsC = random.choice(IELTsc)
							ACTFLC = random.choice(ACTFLc)
							return render(response, "main/results.html", {"TOEFL_ITP":TOEFL_ITP, "CEFR":CEFR, "TOEFL_IBT":TOEFL_IBT, "IELTs":IELTs, "ACTFL":ACTFL, "TOEFL_ITPC":TOEFL_ITPC, "CEFRC":CEFRC, "TOEFL_IBTC":TOEFL_IBTC, "IELTsC":IELTsC, "ACTFLC":ACTFLC})						
						else:
							aop()
							score = score - 13
							print(score)
							print(said)
					except sr.UnknownValueError:
						print("Next question.")
						err = err + 1
						if err == 5:
							speak("I'm sorry but we need to start the test from the beginning. Click play to start with question 1. I recommend that you use a different microphone source to continue.")
							score = 0
						else:
							aop()
							score = score - 13
					except sr.RequestError as e:
						print("Expetion:" + str(e))
					
		if response.POST.get("Question"):
			messages.success(response, f'Press record to start speaking your answer.')			
			if score == 0:
				print("Test")
				score = score + 1
				print(score)
				questionA1_1()
			if score == 2:
				score = score + 1
				print(score)
				questionA1_2()
			if score == 4:
				score = score + 1
				print(score)				
				questionA1_3()
			if score == 6:
				score = score + 1
				print(score)
				questionA1_4()
			if score == 8:
				score = score + 1
				print(score)
				questionA1_5()
			if score == 10:
				score = score + 1
				print(score)
				questionA1_6()
			if score == 12:
				score = score + 1
				print(score)
				questionA1_7()
			if score == 14:
				score = score + 1
				print(score)
				questionA1_8()
			if score == 16:
				score = score + 1
				print(score)
				questionA1_9()
			if score == 18:
				score = score + 1
				print(score)
				questionA1_10()
			if score == 20:
				score = score + 1
				print(score)
				questionA1_11()
			if score == 22:
				score = score + 1
				print(score)
				questionA1_12()
			if score == 24:
				score = score + 1
				print(score)
				questionA1_13()
			if score == 26:
				score = score + 1
				print(score)
				questionA1_14()
				#End A1
				#Begin A2 test
			if score == 28:
				score = score + 1
				print(score)
				questionA2_1()
			if score == 30:
				score = score + 1
				print(score)
				questionA2_2()
			if score == 32:
				score = score + 1
				print(score)
				questionA2_3()
			if score == 34:
				score = score + 1
				print(score)
				questionA2_4()
			if score == 36:
				score = score + 1
				print(score)
				questionA2_5()
			if score == 38:
				score = score + 1
				print(score)
				questionA2_6()
			if score == 40:
				score = score + 1
				print(score)
				questionA2_7()
			if score == 42:
				score = score + 1
				print(score)
				questionA2_8()
			if score == 44:
				score = score + 1
				print(score)
				questionA2_9()
			if score == 46:
				score = score + 1
				print(score)
				questionA2_10()
			if score == 48:
				score = score + 1
				print(score)
				questionA2_11()
			if score == 50:
				score = score + 1
				print(score)
				questionA2_12()
			if score == 52:
				score = score + 1
				print(score)
				questionA2_13()
			if score == 54:
				score = score + 1
				print(score)
				questionA2_14()
				#End A2 Test

				#Begin B1 Test
			if score == 56:
				score = score + 1
				print(score)				
				questionB1_1()
			if score == 58:
				score = score + 1
				print(score)
				questionB1_2()
			if score == 60:
				score = score + 1
				print(score)
				questionB1_3()
			if score == 62:
				score = score + 1
				print(score)
				questionB1_4()
			if score == 64:
				score = score + 1
				print(score)
				questionB1_5()
			if score == 66:
				score = score + 1
				print(score)
				questionB1_6()
			if score == 68:
				score = score + 1
				print(score)
				questionB1_7()
			if score == 70:
				score = score + 1
				print(score)
				questionB1_8()
			if score == 72:
				score = score + 1
				print(score)
				questionB1_9()
			if score == 74:
				score = score + 1
				print(score)
				questionB1_10()
			if score == 76:
				score = score + 1
				print(score)
				questionB1_11()
			if score == 78:
				score = score + 1
				print(score)
				questionB1_12()
				#End B1 Test
				#Begin B2 Test
			if score == 80:
				score = score + 1
				print(score)
				questionB2_1()
			if score == 82:
				score = score + 1
				print(score)
				questionB2_2()
			if score == 84:
				score = score + 1
				print(score)
				questionB2_3()
			if score == 86:
				score = score + 1
				print(score)
				questionB2_4()
			if score == 88:
				score = score + 1
				print(score)
				questionB2_5()
			if score == 90:
				score = score + 1
				print(score)
				questionB2_6()
			if score == 92:
				score = score + 1
				print(score)
				questionB2_7()
			if score == 94:
				score = score + 1
				print(score)
				questionB2_8()
			if score == 96:
				score = score + 1
				print(score)
				questionB2_9()
			if score == 98:
				score = score + 1
				print(score)
				questionB2_10()
			
				#end B2 Test
				#Begin C1 Test
			if score == 100:
				score = score + 1
				print(score)
				questionC1_1()
			if score == 102:
				score = score + 1
				print(score)
				questionC1_2()
			if score == 104:
				score = score + 1
				print(score)
				questionC1_3()
			if score == 106:
				score = score + 1
				print(score)
				questionC1_4()
			if score == 108:
				score = score + 1
				print(score)
				questionC1_5()
			if score == 110:
				score = score + 1
				print(score)
				questionC1_6()
			if score == 112:
				score = score + 1
				print(score)
				questionC1_7()
			if score == 114:
				score = score + 1
				print(score)
				questionC1_8()
				#End C1 Test
				#Begin C2 Test
			if score == 116:
				score = score + 1
				print(score)
				questionC2_1()
			if score == 118:
				score = score + 1
				print(score)
				questionC2_2()
			if score == 120:
				score = score + 1
				print(score)
				questionC2_3()
			if score == 122:
				score = score + 1
				print(score)
				questionC2_4()
			if score == 124:
				score = score + 1
				print(score)
				questionC2_5()
			if score == 126:
				score = score + 1
				print(score)
				questionC2_6()	
	print(score)

	return render(response, "main/intro.html", {})



def speak(text):
	tts = gTTS(text=text, lang="en")
	filename = "voice.mp3"
	tts.save(filename)
	playsound.playsound(filename)
	os.remove("voice.mp3")
def questionA1_1():
	random_A1_1 = random.choice(A1_1)
	speak(random_A1_1)

def questionA1_2():
	random_A1_2 = random.choice(A1_2)
	speak(random_A1_2)

def questionA1_3():
	random_A1_3 = random.choice(A1_3)
	speak(random_A1_3)

def questionA1_4():
	random_A1_4 = random.choice(A1_4)
	speak(random_A1_4)

def questionA1_5():
	random_A1_5 = random.choice(A1_5)
	speak(random_A1_5)

def questionA1_6():
	random_A1_6 = random.choice(A1_6)
	speak(random_A1_6)

def questionA1_7():
	random_A1_7 = random.choice(A1_7)
	speak(random_A1_7)

def questionA1_8():
	random_A1_8 = random.choice(A1_8)
	speak(random_A1_8)

def questionA1_9():
	random_A1_9 = random.choice(A1_9)
	speak(random_A1_9)

def questionA1_10():
	random_A1_10 = random.choice(A1_10)
	speak(random_A1_10)

def questionA1_11():
	random_A1_11 = random.choice(A1_11)
	speak(random_A1_11)

def questionA1_12():
	random_A1_12 = random.choice(A1_12)
	speak(random_A1_12)

def questionA1_13():
	random_A1_13 = random.choice(A1_13)
	speak(random_A1_13)

def questionA1_14():
	random_A1_14 = random.choice(A1_14)
	speak(random_A1_14)

#End A1
#Begin A2 test



def questionA2_1():
	random_A2_1 = random.choice(A2_1)
	speak(random_A2_1)

def questionA2_2():
	random_A2_2 = random.choice(A2_2)
	speak(random_A2_2)

def questionA2_3():
	random_A2_3 = random.choice(A2_3)
	speak(random_A2_3)

def questionA2_4():
	random_A2_4 = random.choice(A2_4)
	speak(random_A2_4)

def questionA2_5():
	random_A2_5 = random.choice(A2_5)
	speak(random_A2_5)

def questionA2_6():
	random_A2_6 = random.choice(A2_6)
	speak(random_A2_6)

def questionA2_7():
	random_A2_7 = random.choice(A2_7)
	speak(random_A2_7)

def questionA2_8():
	random_A2_8 = random.choice(A2_8)
	speak(random_A2_8)

def questionA2_9():
	random_A2_9 = random.choice(A2_9)
	speak(random_A2_9)

def questionA2_10():
	random_A2_10 = random.choice(A2_10)
	speak(random_A2_10)

def questionA2_11():
	random_A2_11 = random.choice(A2_11)
	speak(random_A2_11)

def questionA2_12():
	random_A2_12 = random.choice(A2_12)
	speak(random_A2_12)

def questionA2_13():
	random_A2_13 = random.choice(A2_13)
	speak(random_A2_13)

def questionA2_14():
	random_A2_14 = random.choice(A2_14)
	speak(random_A2_14)
#End A2 Test

#Begin B1 Test
def questionB1_1():
	random_B1_1 = random.choice(B1_1)
	speak(random_B1_1)

def questionB1_2():
	random_B1_2 = random.choice(B1_2)
	speak(random_B1_2)

def questionB1_3():
	random_B1_3 = random.choice(B1_3)
	speak(random_B1_3)

def questionB1_4():
	random_B1_4 = random.choice(B1_4)
	speak(random_B1_4)

def questionB1_5():
	random_B1_5 = random.choice(B1_5)
	speak(random_B1_5)

def questionB1_6():
	random_B1_6 = random.choice(B1_6)
	speak(random_B1_6)

def questionB1_7():
	random_B1_7 = random.choice(B1_7)
	speak(random_B1_7)

def questionB1_8():
	random_B1_8 = random.choice(B1_8)
	speak(random_B1_8)

def questionB1_9():
	random_B1_9 = random.choice(B1_9)
	speak(random_B1_9)

def questionB1_10():
	random_B1_10 = random.choice(B1_10)
	speak(random_B1_10)

def questionB1_11():
	random_B1_11 = random.choice(B1_11)
	speak(random_B1_11)

def questionB1_12():
	random_B1_12 = random.choice(B1_12)
	speak(random_B1_12)
#End B1 Test
#Begin B2 Test

def questionB2_1():
	random_B2_1 = random.choice(B2_1)
	speak(random_B2_1)

def questionB2_2():
	random_B2_2 = random.choice(B2_2)
	speak(random_B2_2)

def questionB2_3():
	random_B2_3 = random.choice(B2_3)
	speak(random_B2_3)

def questionB2_4():
	random_B2_4 = random.choice(B2_4)
	speak(random_B2_4)

def questionB2_5():
	random_B2_5 = random.choice(B2_5)
	speak(random_B2_5)

def questionB2_6():
	random_B2_6 = random.choice(B2_6)
	speak(random_B2_6)

def questionB2_7():
	random_B2_7 = random.choice(B2_7)
	speak(random_B2_7)

def questionB2_8():
	random_B2_8 = random.choice(B2_8)
	speak(random_B2_8)

def questionB2_9():
	random_B2_9 = random.choice(B2_9)
	speak(random_B2_9)

def questionB2_10():
	random_B2_10 = random.choice(B2_10)
	speak(random_B2_10)

#end B2 Test
#Begin C1 Test
def questionC1_1():
	random_C1_1 = random.choice(C1_1)
	speak(random_C1_1)

def questionC1_2():
	random_C1_2 = random.choice(C1_2)
	speak(random_C1_2)

def questionC1_3():
	random_C1_3 = random.choice(C1_3)
	speak(random_C1_3)

def questionC1_4():
	random_C1_4 = random.choice(C1_4)
	speak(random_C1_4)

def questionC1_5():
	random_C1_5 = random.choice(C1_5)
	speak(random_C1_5)

def questionC1_6():
	random_C1_6 = random.choice(C1_6)
	speak(random_C1_6)

def questionC1_7():
	random_C1_7 = random.choice(C1_7)
	speak(random_C1_7)

def questionC1_8():
	random_C1_8 = random.choice(C1_8)
	speak(random_C1_8)
#End C1 Test
#Begin C2 Test

def questionC2_1():
	random_C2_1 = random.choice(C2_1)
	speak(random_C2_1)

def questionC2_2():
	random_C2_2 = random.choice(C2_2)
	speak(random_C2_2)

def questionC2_3():
	random_C2_3 = random.choice(C2_3)
	speak(random_C2_3)

def questionC2_4():
	random_C2_4 = random.choice(C2_4)
	speak(random_C2_4)

def questionC2_5():
	random_C2_5 = random.choice(C2_5)
	speak(random_C2_5)

def questionC2_6():
	random_C2_6 = random.choice(C2_6)
	speak(random_C2_6)

def good():
	random_goods = random.choice(goods)
	speak(random_goods)

def aop():
	random_aops = random.choice(aops)
	speak(random_aops)

goods = [
"Reviewing this response is easy, you spoke very clearly. Click Play for the next task.",
"The key tu success is to speak as clear as possible. Click Play for the next task.",
"I'm not having any difficulties grading your response, keep speaking clearly. Click Play for the next task.",
"Maintain a professional tone of voice and you'll get far; I'm not talking only about the test... Click Play for the next task",
"I don't know, if I'm allowed to say this!! But... you nailed that question!",
"Keep up your, great tone of voice, so I can grade you better!",
"The key to a speaking test, is to speak clearly.",
"Click Play to listen to the next task.",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"So far so good. Click Play to listen to the next task",
"'Everybody is a genius. But if you judge a fish by its ability to climb a tree, it will spend its whole life believing that it is stupid.'' – Albert Einstein",
"'My advice is, never do tomorrow, what you can do today. Procrastination is the thief of time.'' – Charles Dickens and 'David Copperfield'",
"'Success consists of going from failure to failure without loss of enthusiasm.'' – Winston Churchill. Click play to listen to the next task",
"'You may encounter many defeats, but you must not be defeated. In fact, it may be necessary to encounter the defeats, so you can know, who you are, what you can rise from, how you can still come out of it.' —Maya Angelou",
"'Trust yourself. You know more than you think you do.' – Benjamin Spock",
"Remember that, as your test examenier, I'm not only grading your English Level, but, also, your quality of speech.",
]
aops = [
"Better luck next time!",
"Continue improving your skills, you will make it really far if you do!",
"The decision that will cost you the most is not acting on what you want to achieve.",
"Anybody can fail, it's how you stand up that matters.",
"Don't think the path will be easy or hard. Instead, enjoy every minute of it.",
"The decision to continue is what defines you from the rest.",
"I recommend that you practice your English skills further!",
"Remember that He, she, it, is, and I, you, we, they, are.",
"The best thing we can do is continue preparing for future obstacles",
"Never let anyone tell you what you can or cannot do. Instead, prove it to yourself.",
"I might be a computer program, but even I know that you have potential! Use it!",
"In Platinum Language Institute we have amazing programs that can improve your level drastically.",
"There is always something new we can learn!",
"Don't be nervous to answer sometimes we win, sometimes we lose.",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task",
"Click Play to listen to the next task"
]
introductions = [
'Hey there! My name is Lia, and I will be your test moderator today. . . This English Level Test evaluates your conversation and listening skills. . . This evaluation is aligned to common tests, and references such as the CEFR, TOEFL, ACTFL, and, IELTs. . . The test runs in an amazingly simple way. First, I will say a sentence, a question or a small text, and you will need to respond via the microphone. . . You will need to have some sort of headset with a microphone for better results. . . As soon as you click the Play button, I will start speaking, and give you instructions on what to answer. . . When you click on the Recoord button, I will enable your microphone for you to start speaking! As soon as you stop talking I will save your response and evaluate it, feel free to press play again for the next question. . . Ok then, GOOD LUCK!!!',
'Hello there! My name is Emma, and I will be your test moderator today. . . This E...L...T... evaluates your conversation and listening skills. . . This evaluation is aligned to common tests and references such as the CEFR, TOEFL, ACTFL, and, IELTs. . . The test runs in a remarkably simple way. First, I will say a sentence, a question or a small text, and you will need to respond via the microphone. . . You will need to have some sort of headset with a microphone for better results. . . As soon as you click the Play button, I will start speaking, and give you instructions on what to answer. . . When you click on the Recoord button, I will enable your microphone for you to start speaking! As soon as you stop talking I will save your response and evaluate it, feel free to press play again for the next question. . . Ok then, GOOD LUCK!!!'
]

A1_1 = [
"-.-.-.-.-.-,Please repeat this sentence... Hello! My name is Luis",
"-.-.-.-.-.-,Please repeat this sentence... Hey there! My name is Monica",
"-.-.-.-.-.-,Please repeat this sentence... How are you doing today?"
]

A1_1_A = [
"hello my name is Luis",
"hey there my name is Monica",
"how are you doing today"
]

A1_2 = [
"-.-.-.-.-.-,Please repeat the last four digits of this phone number-.-.-.-.-.-,... -.-.-.-.-.-,614-335-1766",
"-.-.-.-.-.-,Please repeat the numbers that sound more than once in order-.-.-.-.-.-,... -.-.-.-.-.-,614-335-1766"
]

A1_2_A = ['1766',
'one seven six six',
"seventeen sixty-six",
"136",
"one three six",
"13 + 6 ",
"one three and six"
]

A1_3 = [
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,When are you going to go out?",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,I work tomorrow",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,Did you finish your project?"
]

A1_3_A = [
'when are you going to go out',
"I work tomorrow"
"did you finish your project"
]

A1_4 = [
'-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,I was created by platinum language institute.',
'-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,I was created in the year 2020.'
]

A1_4_A = [
'I was created by platinum language institute',
'I was created by Platinum Language Institute',
'I was created in the year 2020'
]

A1_5 = [
'-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,My favorite book is about wizards.',
'-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,My favorite movie is about superheroes',
'-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,My favorite food is pizza',
'-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,My favorite season is winter'
]

A1_5_A = [
'my favorite book is about wizards',
'my favorite movie is about superheroes',
'my favorite food is pizza',
'my favorite season is winter'
]

A1_6 = [
'-.-.-.-.-.-,Please answer the question-.-.-.-.-.-,. -.-.-.-.-.-,How, are, you?'
]

A1_6_A = [
"I'm doing fine thank you what about you",
"I'm okay thanks",
"I'm good",
"I'm okay"
]

A1_7 = [
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,I usually have some coffee and toast for my breakfast.",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,I'm trying to eat a healthier diet.",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,He's never been to New York.",
]

A1_7_A = [
"I usually have some coffee and toast for my breakfast",
"I'm trying to eat a healthier diet",
"he's never been to New York",
]

A1_8 = [
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,At this rate, they will never be here on time.",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,Have you studied Chinese before?",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,I can do that for you."
]

A1_8_A = [
"at this rate they will never be here on time",
"have you studied Chinese before",
"I can do that for you"
]

A1_9 = [
"-.-.-.-.-.-,Repeat the word that is most nearly opposie in meaning to 'debate'-.-.-.-.-.-,... -.-.-.-.-.-,agree-.-.-.-.-.-,. -.-.-.-.-.-,tame-.-.-.-.-.-,. -.-.-.-.-.-,dispute-.-.-.-.-.-,. -.-.-.-.-.-,ignore.",
"-.-.-.-.-.-,Repeat the word that is most nearly opposie in meaning to 'havoc'-.-.-.-.-.-,... -.-.-.-.-.-,wonder-.-.-.-.-.-,. -.-.-.-.-.-,peace-.-.-.-.-.-,. -.-.-.-.-.-,chaos-.-.-.-.-.-,. -.-.-.-.-.-,warfare.",
]

A1_9_A = [
"agree",
"peace",
]

A1_10 = [
"-.-.-.-.-.-,Please repeat the following number-.-.-.-.-.-,. -.-.-.-.-.-,614-503-6372",
"-.-.-.-.-.-,Please repeat the following number-.-.-.-.-.-,. -.-.-.-.-.-,614-335-1766",
"-.-.-.-.-.-,Please repeat the following number-.-.-.-.-.-,. -.-.-.-.-.-,614-335-3827"
]

A1_10_A = [
"614-503-6372",
"614-335-1766",
"614-335-3827"
]

A1_11= [
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,How was your day today?",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,What did you do on your last vacation?",
]

A1_11_A = [
"how was your day today",
"what did you do on your last vacation",
]

A1_12 = [
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,My day was amazing thank you for asking.",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,. -.-.-.-.-.-,I went to London with my family.",
]

A1_12_A = [
"my day was amazing thank you for asking",
"I went to London with my family",
]

A1_13 = [
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,... -.-.-.-.-.-,How far is it from Hong Kong to Shanghai?",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,... -.-.-.-.-.-,When we finish the painting, we'll have a cup of tea.",
]

A1_13_A = [
"how far is it from Hong Kong to Shanghai",
"when we finish the painting, we'll have a cup of tea",
]

A1_14 = [
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,... -.-.-.-.-.-,You didn't have to do that, you know.",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,... -.-.-.-.-.-,He would love her forever.",
"-.-.-.-.-.-,Please repeat this sentence-.-.-.-.-.-,... -.-.-.-.-.-,She asked the shop assistant for a refund."
]

A1_14_A = [
"you didn't have to do that you know",
"he would love her forever",
"she asked the shop assistant for a refund"
]



A2_1 = [
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,When are we going to go out-.-.-.-.-.-,??? -.-.-.-.-.-,When going out are we-.-.-.-.-.-,??? -.-.-.-.-.-,When do we going out???",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,I work tomorrow-.-.-.-.-.-,... -.-.-.-.-.-,I don't working tomorrow-.-.-.-.-.-,... -.-.-.-.-.-,I'm work tomorrow."
]

A2_1_A = [
"I work tomorrow",
"when are we going to go out"
]

A2_2 = [
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,Did you finishing your project-.-.-.-.-.-,??? -.-.-.-.-.-,Have you finished your project-.-.-.-.-.-,??? -.-.-.-.-.-,Have you got finish your project?",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,I am usually having some coffee and toast for my breakfast-.-.-.-.-.-,... -.-.-.-.-.-,I am used to have some coffee and toast for my breakfast-.-.-.-.-.-,... -.-.-.-.-.-,I usually have some coffee and toast for my breakfast"
]

A2_2_A = [
'have you finished your project',
'I usually have some coffee and toast for my breakfast'
]

A2_3 = [
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,I'm trying to eat a more healthy diet-.-.-.-.-.-,... -.-.-.-.-.-,I try to eat a more healthy diet-.-.-.-.-.-,... -.-.-.-.-.-,I'm trying to eat a healthier diet.",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,He's never been to New York-.-.-.-.-.-,... -.-.-.-.-.-,He's never gone to New York."
]

A2_3_A = [
"I'm trying to eat a healthier diet",
"he's never been to New York"
]

A2_4 = [
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,At this rate, they will never be here on time-.-.-.-.-.-,... -.-.-.-.-.-,At this rate, they are never here on time.",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,Are you studied Chinese before-.-.-.-.-.-,??? -.-.-.-.-.-,Have you studied Chinese before?"
]

A2_4_A = [
"at this rate they will never be here on time",
"have you studied Chinese before"
]

A2_5 = [
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,I can do that for you-.-.-.-.-.-,... -.-.-.-.-.-,I could do that-.-.-.-.-.-,... -.-.-.-.-.-,I could to make that for you.",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,Thank you, that are very kind-.-.-.-.-.-,... -.-.-.-.-.-,Thank you, that's very kind."
]

A2_5_A = [
"I can do that for you",
"thank you that's very kind"
]

A2_6 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,Are you going to University-.-.-.-.-.-,??? -.-.-.-.-.-,Are you going to go to the University-.-.-.-.-.-,??? -.-.-.-.-.-,Do you like University?",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,You haven't to do that - you know-.-.-.-.-.-,... -.-.-.-.-.-,You didn't have to do that - you know-.-.-.-.-.-,... -.-.-.-.-.-,You didn't must do that - you know."
]

A2_6_A = [
"are you going to go to the university",
"you didn't have to do that you know"
]

A2_7 = [
"-.-.-.-.-.-,Repeat the correct sentence referring to distance-.-.-.-.-.-,... -.-.-.-.-.-,How long is it from Hong Kong to Shanghai-.-.-.-.-.-,??? -.-.-.-.-.-,How far is it from Hong Kong to Shanghai-.-.-.-.-.-,??? -.-.-.-.-.-,How much is it from Hong Kong to Shanghai-.-.-.-.-.-,?",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-,... -.-.-.-.-.-,When we finish the painting, we'll have a cup of tea-.-.-.-.-.-,. -.-.-.-.-.-,When we've finished the painting, we'll have a cup of tea-.-.-.-.-.-,. -.-.-.-.-.-,When the painting finishes, we'll have a cup of tea-.-.-.-.-.-,."
]

A2_7_A = [
"how far is it from Hong Kong to Shanghai",
"when we finish the painting we'll have a cup of tea"
]

A2_8 = [
"-.-.-.-.-.-,Complete this fragment by repeating the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,'He told her that...'-.-.-.-.-.-,. -.-.-.-.-.-,He would love her forever-.-.-.-.-.-,... -.-.-.-.-.-,He loved her forever-.-.-.-.-.-,... -.-.-.-.-.-,He is loving her forever.",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,She asked the shop assistant to have a refund-.-.-.-.-.-,... -.-.-.-.-.-,She asked the shop assistant to give a refund-.-.-.-.-.-,... -.-.-.-.-.-,She asked the shop assistant for a refund."
]

A2_8_A = [
"he would love her forever",
"she asked the shop assistant for a refund"
]

A2_9 = [
"-.-.-.-.-.-,Repeat the word that is most nearly similar to 'Excavate...'-.-.-.-.-.-,. -.-.-.-.-.-,scrape-.-.-.-.-.-,... -.-.-.-.-.-,hollow-.-.-.-.-.-,... -.-.-.-.-.-,bury-.-.-.-.-.-,... -.-.-.-.-.-,mask.",
"-.-.-.-.-.-,Repeat the word that is most nearly similar to 'Absurd...'-.-.-.-.-.-,. -.-.-.-.-.-,batty-.-.-.-.-.-,... -.-.-.-.-.-,sensible-.-.-.-.-.-,... -.-.-.-.-.-,certain-.-.-.-.-.-,... -.-.-.-.-.-,insane."
]

A2_9_A = [
"scrape",
"insane",
"batty"
]

A2_10 = [
"-.-.-.-.-.-,Repeat the word that is most nearly opposite to 'Pedestrian...'-.-.-.-.-.-,. -.-.-.-.-.-,motorist-.-.-.-.-.-,... -.-.-.-.-.-,hiker-.-.-.-.-.-,... -.-.-.-.-.-,galloper-.-.-.-.-.-,... -.-.-.-.-.-,sailor.",
"-.-.-.-.-.-,Repeat the word that is most nearly opposite to 'Solitary-.-.-.-.-.-,...'-.-.-.-.-.-,. -.-.-.-.-.-,friendly-.-.-.-.-.-,... -.-.-.-.-.-,lonely-.-.-.-.-.-,... -.-.-.-.-.-,isolated-.-.-.-.-.-,... -.-.-.-.-.-,together."
]

A2_10_A = [
"motorist",
"friendly"
]

A2_11= [
"-.-.-.-.-.-,Repeat the word that is most nearly opposite to 'Soar...'-.-.-.-.-.-,. -.-.-.-.-.-,elevate-.-.-.-.-.-,... -.-.-.-.-.-,float-.-.-.-.-.-,... -.-.-.-.-.-,mount-.-.-.-.-.-,... -.-.-.-.-.-,land.",
"-.-.-.-.-.-,Repeat the word that is most nearly opposite to 'Athletic...'-.-.-.-.-.-,. -.-.-.-.-.-,frail-.-.-.-.-.-,... -.-.-.-.-.-,muscular-.-.-.-.-.-,... -.-.-.-.-.-,energetic-.-.-.-.-.-,... -.-.-.-.-.-,intelligent."
]

A2_11_A = [
"land",
"frail"
]

A2_12 = [
"-.-.-.-.-.-,Repeat the word that is most nearly opposite to 'Criticize...'-.-.-.-.-.-,. -.-.-.-.-.-,punish-.-.-.-.-.-, -.-.-.-.-.-,praise-.-.-.-.-.-,... -.-.-.-.-.-,blame-.-.-.-.-.-,... -.-.-.-.-.-,approve.",
"-.-.-.-.-.-,Repeat the word that is most nearly opposite to 'Accomplish...'-.-.-.-.-.-,. -.-.-.-.-.-,exhaust-.-.-.-.-.-,... -.-.-.-.-.-,manage-.-.-.-.-.-,... -.-.-.-.-.-,blunder-.-.-.-.-.-,... -.-.-.-.-.-,cease."
]

A2_12_A = [
"praise",
"cease"
]

A2_13 = [
"-.-.-.-.-.-,Repeat the sentence that best describes the meaning of-.-.-.-.-.-, -.-.-.-.-.-,'success...'-.-.-.-.-.-,. -.-.-.-.-.-,The accomplishment of an aim or purpose-.-.-.-.-.-,... -.-.-.-.-.-,Failing but then trying again-.-.-.-.-.-,... -.-.-.-.-.-,Try to not give up.",
"-.-.-.-.-.-,Repeat the sentence that best describes the meaning of-.-.-.-.-.-, -.-.-.-.-.-,'failure...'. -.-.-.-.-.-,The omission of expected or required action-.-.-.-.-.-, -.-.-.-.-.-,the accomplishment of an aim or purpose."
]

A2_13_A = [
"the accomplishment of an aim or purpose",
"the omission of expected or required action"
]

A2_14 = [
"-.-.-.-.-.-,In this section, you need to: Listen to the advertisement, and then answer the question-.-.-.-.-.-,... Sixteen... What now? You're 16 and finally you can leave school! By now, you're probably sick of teachers, desks, tests, and exams... But, don't just run for the exit. You need to think carefully about what to do next. If you want a professional career, you will need to go to the university and get a degree. To do that, you need to stay at high school for another two years... But, you needn't stay at the same place. There are several options in the district of North acre. St. Leopold's School has the best pass rate of all the high schools in the district. It offers a wide range of subjects in the humanities and sciences. St. Leopold's is of course, a private school, so it may be too expensive for you. But don't worry, there are several other options, if you want to follow the academic route. Knowle Grammar School is a state school, so there are no fees, and it has excellent tuition, and facilities. It is a boys' school from the ages of 11-16, but from 16-18 it is co-educational. However, it is selective, so you’ll have to pass an exam to get in. If you're interested in going into Business, check out Wyle River Academy. This school specializes in subjects like; Business Studies, Management, and Economics. If you prefer the arts, look at the courses on offer at North acre College. Here you can study; woodwork, art, textiles, and much more. North acre College also offers a wide range of vocational qualifications. You can do a 1-year certificate, or a 2-year diploma in subjects like; electrics, plumbing, roofing, and hairdressing. If you'd prefer to work outdoors - look at Milltown College, where there are courses in Farm Mechanics, Land Management, Animal Management, and much more. A final option is to get an apprenticeship with a local or national company. You will get on-the-job training, gain certificates, or diplomas, and start earning straight away. But be warned - places are limited! Find out more at the Job Fair on May 26th at North acre College-.-.-.-.-.-,... -.-.-.-.-.-,Answer this question-.-.-.-.-.-,!!! -.-.-.-.-.-,The aim of the advertisement, is - to-.-.-.-.-.-,... -.-.-.-.-.-,Advise young people about how to get to university-.-.-.-.-.-,... -.-.-.-.-.-,Tell young people about the options available-.-.-.-.-.-,... -.-.-.-.-.-,Advise young people to stay in education."
]

A2_14_A = [
"tell young people about the options available"
]




B1_1 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,He told he wasn't feeling well-.-.-.-.-.-, -.-.-.-.-.-,He said he doesn't feeling well-.-.-.-.-.-, -.-.-.-.-.-,He said he wasn't feeling well.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,We won't know how to do after we get the results-.-.-.-.-.-, -.-.-.-.-.-,We won't know what to do until we get the results."
]

B1_1_A = [
"he said he wasn't feeling well",
"we won't know what to do until we get the results"
]

B1_2 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,If you wouldn't tell me, I'll scream-.-.-.-.-.-,!!! -.-.-.-.-.-,If you don't tell me, I'll scream-.-.-.-.-.-,!!! -.-.-.-.-.-,If you didn't tell me, I'll scream!",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,He's probably lost her number-.-.-.-.-.-, -.-.-.-.-.-,He's lost her number probably-.-.-.-.-.-, -.-.-.-.-.-,Probably he's lost her number."
]

B1_2_A = [
"if you don't tell me I'll scream",
"he's probably lost her number"
]

B1_3 = [
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-, -.-.-.-.-.-,is-.-.-.-.-.-, -.-.-.-.-.-,American-.-.-.-.-.-, -.-.-.-.-.-,her-.-.-.-.-.-, -.-.-.-.-.-,second-.-.-.-.-.-, -.-.-.-.-.-,husband-.-.-.-.-.-,",
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-, -.-.-.-.-.-,he-.-.-.-.-.-, -.-.-.-.-.-,dances-.-.-.-.-.-, -.-.-.-.-.-,beautifully-.-.-.-.-.-, -.-.-.-.-.-,the-.-.-.-.-.-, -.-.-.-.-.-,Waltz-.-.-.-.-.-,"
]

B1_3_A = [
"is her second husband American",
"he dances the waltz beautifully"
]

B1_4 = [
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-, -.-.-.-.-.-,about-.-.-.-.-.-, -.-.-.-.-.-,what-.-.-.-.-.-, -.-.-.-.-.-,is-.-.-.-.-.-, -.-.-.-.-.-,the-.-.-.-.-.-, -.-.-.-.-.-,movie-.-.-.-.-.-,",
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-, -.-.-.-.-.-,what-.-.-.-.-.-, -.-.-.-.-.-,mean-.-.-.-.-.-, -.-.-.-.-.-,does-.-.-.-.-.-, -.-.-.-.-.-,glitterati-.-.-.-.-.-,"
]

B1_4_A = [
"what is the movie about",
"what does glitterati mean"
]

B1_5 = [
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-, -.-.-.-.-.-,I-.-.-.-.-.-, -.-.-.-.-.-,like-.-.-.-.-.-, -.-.-.-.-.-,very-.-.-.-.-.-, -.-.-.-.-.-,much-.-.-.-.-.-, -.-.-.-.-.-,this-.-.-.-.-.-, -.-.-.-.-.-,restaurant-.-.-.-.-.-,",
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-, -.-.-.-.-.-,almost-.-.-.-.-.-, -.-.-.-.-.-,he-.-.-.-.-.-, -.-.-.-.-.-,missed-.-.-.-.-.-, -.-.-.-.-.-,the-.-.-.-.-.-, -.-.-.-.-.-,flight-.-.-.-.-.-,"
]

B1_5_A = [
"I like this restaurant very much.",
"he almost missed the flight"
]

B1_6 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,I've met him since I was a little girl-.-.-.-.-.-, -.-.-.-.-.-,I've known him since I was a little girl.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,He told us that he would be here later-.-.-.-.-.-, -.-.-.-.-.-,He said us that he would be here later."
]

B1_6_A = [
"I've known him since I was a little girl",
"he told us that he would be here later"
]

B1_7 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,We met when we were doing an exam-.-.-.-.-.-, -.-.-.-.-.-,We met when we where making an exam.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,It doesn't mind if we arrive a bit late-.-.-.-.-.-, -.-.-.-.-.-,It doesn't matter if we arrive a bit late."
]

B1_7_A = [
"we met when we were doing an exam",
"it doesn't matter if we arrive a bit late"
]

B1_8 = [
"-.-.-.-.-.-,In 20 seconds explain how you last vacations where.",
"-.-.-.-.-.-,In 25 second explain what you like the most about the city you live in."
]

B1_8_A = [
#Lia will listen to you response and grade it#
#Emma will listen to your response and grade it#
]

B1_9 = [
"-.-.-.-.-.-,Listen carefuly to this job application form - extract-.-.-.-.-.-,. -.-.-.-.-.-,When I finish talking, press recoord and answer this question, by saying either-.-.-.-.-.-, -.-.-.-.-.-,'yes'-.-.-.-.-.-, or -.-.-.-.-.-,'no'-.-.-.-.-.-,... -.-.-.-.-.-,Has the candidate worked as an accountant before-.-.-.-.-.-,??? I'm interested in this job, because I'm currently looking for an opportunity - to use the skills I learnt in my college. I have recently completed a 16-week part-time accounting course (AAT Level 2 Certificate). The course covered book-keeping, recording income and receipts, and basic costing. We used a wide range of computer packages, and I picked up the accounting skills easily. I was able to work alone with very little extra help. I passed the course with merit. I believe my success was due to my thorough work, my numeracy skills, and my attention to detail. During the course, I had experience of working to deadlines, and working under pressure. Although this was sometimes stressful, I always completed my work on time. Unfortunately, the course did not include a work placement, so I have not practiced my skills in a business setting, and I am now looking for an opportunity to do so. I am particularly looking for a job in a small company such as yours, as I believe I will be able to interact with a wider range of people, and as a result, learn more skills. I would like to progress within a company, and gain more responsibilities over the years. Although I do not have work experience in finance, I have experience in working in an office environment. Before starting the accounting course, I worked for 6 months in a recruitment office as a receptionist... My duties involved meeting and greeting clients and visitors, taking phone calls, audio, and copy typing and checking stock. I also had to keep the petty cash and mail records. Through this work, I developed my verbal and written communication skills. I had to speak confidently to strangers and deliver clear messages. I enjoyed working in a team environment. I believe the office appreciated my friendly manner, and efficient work-.-.-.-.-.-,... -.-.-.-.-.-,Answer this question, by saying-.-.-.-.-.-,'yes'-.-.-.-.-.-, or -.-.-.-.-.-,'no'-.-.-.-.-.-, -.-.-.-.-.-,Has the candidate worked as an accountant before?"
]

B1_9_A = [
"no",
"no she hasn't",
"no she has not"
]

B1_10 = [
"-.-.-.-.-.-,Listen carefuly to this job application form - extract-.-.-.-.-.-,. -.-.-.-.-.-,When I finish talking, press recoord and answer this question, by saying either-.-.-.-.-.-, -.-.-.-.-.-,'yes'-.-.-.-.-.-, or -.-.-.-.-.-,'no'-.-.-.-.-.-,... -.-.-.-.-.-,Is the candidate applying to a large firm-.-.-.-.-.-,??? I'm interested in this job, because I'm currently looking for an opportunity - to use the skills I learnt in my college. I have recently completed a 16-week part-time accounting course (AAT Level 2 Certificate). The course covered book-keeping, recording income and receipts, and basic costing. We used a wide range of computer packages, and I picked up the accounting skills easily. I was able to work alone with very little extra help. I passed the course with merit. I believe my success was due to my thorough work, my numeracy skills, and my attention to detail. During the course, I had experience of working to deadlines, and working under pressure. Although this was sometimes stressful, I always completed my work on time. Unfortunately, the course did not include a work placement, so I have not practiced my skills in a business setting, and I am now looking for an opportunity to do so. I am particularly looking for a job in a small company such as yours, as I believe I will be able to interact with a wider range of people, and as a result, learn more skills. I would like to progress within a company, and gain more responsibilities over the years. Although I do not have work experience in finance, I have experience in working in an office environment. Before starting the accounting course, I worked for 6 months in a recruitment office as a receptionist... My duties involved meeting and greeting clients and visitors, taking phone calls, audio, and copy typing and checking stock. I also had to keep the petty cash and mail records. Through this work, I developed my verbal and written communication skills. I had to speak confidently to strangers and deliver clear messages. I enjoyed working in a team environment. I believe the office appreciated my friendly manner, and efficient work-.-.-.-.-.-,... -.-.-.-.-.-,Answer this question, by saying-.-.-.-.-.-,'yes'-.-.-.-.-.-, or -.-.-.-.-.-,'no'-.-.-.-.-.-, -.-.-.-.-.-,Is the candidate applying to a large firm?",
]

B1_10_A = [
"no",
"no she isn't",
"no she is not"
]

B1_11= [
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-,  -.-.-.-.-.-,he-.-.-.-.-.-, -.-.-.-.-.-,has-.-.-.-.-.-, -.-.-.-.-.-,lost-.-.-.-.-.-, -.-.-.-.-.-,his-.-.-.-.-.-, -.-.-.-.-.-,keys-.-.-.-.-.-, -.-.-.-.-.-,probably-.-.-.-.-.-,",
"-.-.-.-.-.-,Put the words in the correct order and say the sentence-.-.-.-.-.-,  -.-.-.-.-.-,he-.-.-.-.-.-, -.-.-.-.-.-,didn't-.-.-.-.-.-, -.-.-.-.-.-,say-.-.-.-.-.-, -.-.-.-.-.-,goodbye-.-.-.-.-.-, -.-.-.-.-.-,even."
]

B1_11_A = [
"he has probably lost his keys",
"he didn't even say goodbye"
]

B1_12 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,They won a lot of money in the Lottery-.-.-.-.-.-, -.-.-.-.-.-,They earned a lot of money in the Lottery.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,We are expecting some visitors this weekend-.-.-.-.-.-, -.-.-.-.-.-,We are hoping some visitors this weekend."
]

B1_12_A = [
"they won a lot of money in the lottery",
"we are expecting some visitors this weekend"
]


B2_1 = [
"Explain in 25 seconds why you are taking this test...",
"Explain in 20 seconds your goals 5 years from now..."
]

B2_1_A = [
#Lia will evaluate your response#
#Emma will evaluate your response#
]

B2_2 = [
"-.-.-.-.-.-,Complete the fragment by speaking the answer-.-.-.-.-.-, -.-.-.-.-.-,'All my life...'. -.-.-.-.-.-,I love going to the movies-.-.-.-.-.-, -.-.-.-.-.-,I have loved to go to the movies-.-.-.-.-.-, -.-.-.-.-.-,I've loved going to the movies.",
"-.-.-.-.-.-,Complete the fragment by speaking the answer-.-.-.-.-.-, -.-.-.-.-.-,'He's had his car...'. -.-.-.-.-.-,when he passed his driving test-.-.-.-.-.-, -.-.-.-.-.-,since he passed his driving test-.-.-.-.-.-, -.-.-.-.-.-,as he passed his driving test..."
]

B2_2_A = [
"all my life I've loved going to the movies",
"I've loved going to the movies",
"I have loved going to the movies",
"all my life I have loved going to the movies",
"he's had his car since he passed his driving place",
"since he passed his driving place"
]

B2_3 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,Your birthday's next month, isn't it??? -.-.-.-.-.-,Your birthday going to be next month, won't it??? -.-.-.-.-.-,Your birthday is going to be next month, isn't it?",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,He looks just as his father-.-.-.-.-.-, -.-.-.-.-.-,He looks just like his father-.-.-.-.-.-, -.-.-.-.-.-,He looks just after his father."
]

B2_3_A = [
"your birthday is going to be next month isn't it",
"He looks just like his father"
]

B2_4 = [
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to cut tooth-.-.-.-.-.-, -.-.-.-.-.-,to cut house-.-.-.-.-.-, -.-.-.-.-.-,to cut precautions.",
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to read a tooth-.-.-.-.-.-, -.-.-.-.-.-,to read between the lines-.-.-.-.-.-, -.-.-.-.-.-,to read time..."
]

B2_4_A = [
"to cut tooth",
"to read between the lines"
]

B2_5 = [
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to form an opinion-.-.-.-.-.-, -.-.-.-.-.-,to form allowances-.-.-.-.-.-, -.-.-.-.-.-,to form precautions.",
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to lay the table-.-.-.-.-.-, -.-.-.-.-.-,to lay a company-.-.-.-.-.-, -.-.-.-.-.-,to lay house."
]

B2_5_A = [
"to form an opinion",
"to lay the table"
]

B2_6 = [
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to break a leg-.-.-.-.-.-, -.-.-.-.-.-,to break truant-.-.-.-.-.-, -.-.-.-.-.-,to break a tooth.",
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to play truant-.-.-.-.-.-, -.-.-.-.-.-,to play a vacancy-.-.-.-.-.-, -.-.-.-.-.-,to play time."
]

B2_6_A = [
"to break a leg",
"to play truant"
]

B2_7 = [
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to save time-.-.-.-.-.-, -.-.-.-.-.-,to save a leg-.-.-.-.-.-, -.-.-.-.-.-,to save a tooth.",
"-.-.-.-.-.-,Repeat the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to take allowances-.-.-.-.-.-, -.-.-.-.-.-,to take a vacancy-.-.-.-.-.-, -.-.-.-.-.-,to take precautions."
]

B2_7_A = [
"to save time",
"to take precautions"
]

B2_8 = [
"-.-.-.-.-.-,Listen to the job advertisement, and answer the question-.-.-.-.-.-,... -.-.-.-.-.-,IT Recruitment Officer-.-.-.-.-.-, -.-.-.-.-.-,We are looking for recent graduates, who would like to work with some of the most important companies in the digital industry. This post is based in Dubai. Once you have received training on our computer system, you will be responsible for:- liaising with recruiters to create job descriptions, - advertising jobs, - sourcing possible candidates, - updating the database-.-.-.-.-.-,... We are looking for someone with passion, drive, and commitment. Recruitment Resources must be able to work under pressure, be self-motivated, and people-focused. These qualities will help you progress within the company. Recruitment Resources who are willing to learn can train to become Account Managers, or Account Directors. - Competitive basic salary plus commission-.-.-.-.-.-,... -.-.-.-.-.-,Does this job require you to work alone-.-.-.-.-.-,??? answer with a simple-.-.-.-.-.-, -.-.-.-.-.-,'yes'-.-.-.-.-.-, or -.-.-.-.-.-,'no'.",
"-.-.-.-.-.-,Listen to the job advertisement, and answer the question-.-.-.-.-.-,... -.-.-.-.-.-,IT Recruitment Officer-.-.-.-.-.-, -.-.-.-.-.-,We are looking for recent graduates, who would like to work with some of the most important companies in the digital industry. This post is based in Dubai. Once you have received training on our computer system, you will be responsible for:- liaising with recruiters to create job descriptions, - advertising jobs, - sourcing possible candidates, - updating the database-.-.-.-.-.-,... We are looking for someone with passion, drive, and commitment. Recruitment Resources must be able to work under pressure, be self-motivated, and people-focused. These qualities will help you progress within the company. Recruitment Resources who are willing to learn can train to become Account Managers, or Account Directors. - Competitive basic salary plus commission-.-.-.-.-.-,... -.-.-.-.-.-,Does this job require experience in the building trade-.-.-.-.-.-,??? answer with a simple-.-.-.-.-.-, -.-.-.-.-.-,'yes'-.-.-.-.-.-, or -.-.-.-.-.-,'no'."
]

B2_8_A = [
"no it doesn't",
"no",
"no it does not"
]

B2_9 = [
"-.-.-.-.-.-,Listen to the job advertisement, and answer the question-.-.-.-.-.-,... -.-.-.-.-.-,Project Assistant-.-.-.-.-.-,... -.-.-.-.-.-,Reporting to the Project Manager, you will undertake property surveys, site inspections, and attend site meetings, to ensure that work undertaken by our contractors, is being carried out properly. You must have initiative, as you will be required to work on your own. It is essential that you have your own transportation. An allowance will be provided. Candidates should have: Good keyboard and IT skills, an organized and methodical approach, good written and verbal communication skills. REQUIREMENTS-.-.-.-.-.-, - Minimum 2-year Construction related qualification. - Minimum of 3 year's relevant experience, or transferrable skills from a relevant background-.-.-.-.-.-,... -.-.-.-.-.-,How many years of experience are needed???"
]

B2_9_A = [
"minimum 3 years",
"3 years",
"three years",
"minimum three years",
"3",
"three"
]

B2_10 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,It was really nice of you to invite me-.-.-.-.-.-, -.-.-.-.-.-,It was really nice for you to invite me.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,I'm not very good in math-.-.-.-.-.-, -.-.-.-.-.-,I'm not very good at math."
]

B2_10_A = [
"it was really nice of you to invite me",
"I'm not very good at math"
]


C1_1 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,I think the show is about starting now-.-.-.-.-.-, -.-.-.-.-.-,I think the show is about in start now-.-.-.-.-.-, -.-.-.-.-.-,I think the show is about to start now.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,You wouldn't have heard the news yet-.-.-.-.-.-, -.-.-.-.-.-,You won't have heard the news yet-.-.-.-.-.-, -.-.-.-.-.-,You will have heard the news yet. "
]

C1_1_A = [
"I think the show is about to start now",
"you wouldn't have heard the news yet..."
]

C1_2 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,What do you think you do ten years from now-.-.-.-.-.-, -.-.-.-.-.-,What do you think you'll be doing ten years from now.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,That's a small round Victorian wooden table-.-.-.-.-.-, -.-.-.-.-.-,That's a Victorian small round wooden table-.-.-.-.-.-, -.-.-.-.-.-,That's a Victorian round wooden small table"
]

C1_2_A = [
"what do you think you'll be doing ten years from now",
"that's a small round Victorian wooden table"
]

C1_3 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,I was going to call you but then I forgot-.-.-.-.-.-, -.-.-.-.-.-,I was thinking of call you but then I forgot-.-.-.-.-.-, -.-.-.-.-.-,I was calling you but then I forgot",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,Bicycles are widely used in Amsterdam-.-.-.-.-.-, -.-.-.-.-.-,Bicycles use widely in Amsterdam-.-.-.-.-.-, -.-.-.-.-.-,Bicycles are in use widely in Amsterdam."
]

C1_3_A = [
"I was going to call you but then I forgot",
"bicycles are widely used in Amsterdam"
]

C1_4 = [
"-.-.-.-.-.-,Say the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to throw a party-.-.-.-.-.-, -.-.-.-.-.-,to throw a bear",
"-.-.-.-.-.-,Say the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to alleviate one's suffering-.-.-.-.-.-, -.-.-.-.-.-,to alleviate ones thoughts"
]

C1_4_A = [
"to throw a party",
"to alleviate ones suffering"
]

C1_5 = [
"-.-.-.-.-.-,Say the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to drive a hard bargain-.-.-.-.-.-, -.-.-.-.-.-,to follow a hard bargain-.-.-.-.-.-, -.-.-.-.-.-,to serve a hard bargain.",
"-.-.-.-.-.-,Say the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to cut tooth-.-.-.-.-.-, -.-.-.-.-.-,to collect tooth-.-.-.-.-.-, -.-.-.-.-.-,to alleviate toot."
]

C1_5_A = [
"to drive a hard bargain",
"to cut tooth"
]

C1_6 = [
"-.-.-.-.-.-,Say the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to bear a grudge-.-.-.-.-.-, -.-.-.-.-.-,to serve a grudge...",
"-.-.-.-.-.-,Say the correct phrasal expression-.-.-.-.-.-, -.-.-.-.-.-,to follow suit-.-.-.-.-.-, -.-.-.-.-.-,to take suit..."
]

C1_6_A = [
"to bear a grudge",
"to follow suit"
]

C1_7 = [
"What is your favorite childhood memory?",
"What would you do if you won the lottery today?"
]

C1_7_A = [
#Lia will evaluate your response#,
#Emma will evaluate your response#
]

C1_8 = [
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,I think you might have told me!!! -.-.-.-.-.-,I think you might tell me!!! -.-.-.-.-.-,I think you might to have told me!",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,Michael has come down with a terrible case of flu!!! -.-.-.-.-.-,Michael has bring on with a terrible case of flu!"
]

C1_8_A = [
"I think you might have told me",
"Michael has come down with a terrible case of flu"
]


C2_1 = [
"Where are you from?",
"What is your favorite food?"
]

C2_1_A = [
#Lia will evaluate the response#
#Emma will evaluate the response#
]

C2_2 = [
"Do you consider yourself to be a responsible person?",
"Who do you consider to be your mentor?"
]

C2_2_A = [
#Lia will evaluate the response#
#Emma will evaluate the response#
]

C2_3 = [
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,It's just not worth to get involved-.-.-.-.-.-, -.-.-.-.-.-,It's just not worth getting involved-.-.-.-.-.-, -.-.-.-.-.-,It's just not worth to involve myself",
"-.-.-.-.-.-,Please repeat the correct sentence-.-.-.-.-.-, Sarah got her handbag snatched-.-.-.-.-.-, -.-.-.-.-.-,Sarah had her handbag snatched-.-.-.-.-.-, -.-.-.-.-.-,Sarah's handbag had snatched..."
]

C2_3_A = [
"it's just not worth getting involved",
"Sarah had her handbag snatched"
]

C2_4 = [
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,Cats bring on my terrible allergies-.-.-.-.-.-, -.-.-.-.-.-,Cats break up my terrible allergies.",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,The car was a total do up after the accident-.-.-.-.-.-, -.-.-.-.-.-,The car was a total write off after the accident."
]

C2_4_A = [
"cats bring on my terrible allergies",
"the car was a total write off after the accident"
]

C2_5 = [
"Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,So when do the children come down for Christmas??? -.-.-.-.-.-,So when do the children leave out for Christmas???",
"Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,They have decided to put off their trip to India-.-.-.-.-.-, -.-.-.-.-.-,They have decided to come down their trip to India."
]

C2_5_A = [
"so when do the children come down for Christmas",
"They have decided to put off their trip to India"
]

C2_6 = [
"-.-.-.-.-.-,Repeat the correct sentence... -.-.-.-.-.-,The children were looking after by my mother-.-.-.-.-.-, -.-.-.-.-.-,The children looked after by my mother-.-.-.-.-.-, -.-.-.-.-.-,The children were being looked after by my mother",
"-.-.-.-.-.-,Repeat the correct sentence-.-.-.-.-.-, -.-.-.-.-.-,I think you might have told me!!! -.-.-.-.-.-,I think you might tell me!!! -.-.-.-.-.-,I think you might to have told me!!"
]

C2_6_A = [
"the children were being looked after by my mother",
"I think you might have told me",
"I think you might've told me"
]

global TOEFL_ITP
global TOEFL_IBT
global CEFR
global IELTs
global ACTFL
global TOEFL_ITPC
global TOEFL_IBTC
global CEFRC
global IELTsC
global ACTFLC
global ACTFLc
global IELTsc
global CEFRc
global TOEFLIBT
global TOEFLITP
TOEFLITP = [
"Sorry at this time it is imposible to give you your score please contact support"
]
TOEFLIBT = [
"Sorry at this time it is imposible to give you your score please contact support"
]
CEFRc = [
"Sorry at this time it is imposible to give you your score please contact support"
]
IELTsc = [
"Sorry at this time it is imposible to give you your score please contact support"
]
ACTFLc = [
"Sorry at this time it is imposible to give you your score please contact support"
]
TOEFL_ITP = "no score available"
TOEFL_IBT = "no score available"
CEFR = "no score available"
IELTs = "no score available"
ACTFL = "no score available"
TOEFL_ITPC = random.choice(TOEFLITP)
TOEFL_IBTC = random.choice(TOEFLIBT)
CEFRC = random.choice(CEFRc)
IELTsC = random.choice(IELTsc)
ACTFLC = random.choice(ACTFLc)

