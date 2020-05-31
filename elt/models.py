from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone
from django.urls import reverse
from PIL import Image
from django.conf import settings

# Create your models here.
class ELTcores(models.Model):
	user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="scores", null=True)
	name = models.CharField(max_length=200)
	date_posted = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.name

class Item(models.Model):
	eltcores = models.ForeignKey(ELTcores, on_delete=models.CASCADE)
	text = models.CharField(max_length=300)
	complete = models.BooleanField()
	date_posted = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.text

class Snippet(models.Model):
	title = models.CharField(max_length=100)
	body = models.TextField()
	created = models.DateTimeField(default=timezone.now)

	def __str__(self):
		return self.title

	def body_preview(self):
		return self.body[:50]

class Post(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='authors')
    title = models.CharField(max_length=200)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    likes = models.ManyToManyField(User, related_name='likes', blank=True)
    dislikes = models.ManyToManyField(User, related_name="dislikes", blank=True)
    published_date = models.DateTimeField(blank=True, null=True)

    def publish(self):
        self.published_date = timezone.now()
        self.save()

    def approved_comments(self):
	    return self.comments.filter(approved_comment=True)

    def __str__(self):
        return self.title

class Comment(models.Model):
    post = models.ForeignKey('elt.Post', on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    text = models.TextField()
    created_date = models.DateTimeField(default=timezone.now)
    approved_comment = models.BooleanField(default=False)
    likes = models.ManyToManyField(User, related_name='comment_likes', blank=True)
    dislikes = models.ManyToManyField(User, related_name="comment_dislikes", blank=True)

    def approve(self):
        self.approved_comment = True
        self.save()

    def __str__(self):
        return self.text

