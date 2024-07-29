from django.db import models
from django.contrib.auth.models import User


class Conversations(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    instructions = models.TextField()
    style = models.CharField()
    genre = models.CharField()
    themes = models.CharField()
    keywords = models.CharField()
    idea = models.TextField()
    summary=models.TextField()
    type=models.CharField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.genre} - {self.style}"