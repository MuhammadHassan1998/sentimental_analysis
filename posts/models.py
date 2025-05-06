from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    SENTIMENT_CHOICES = [
        ("Positive", "Positive"),
        ("Negative", "Negative"),
        ("Neutral", "Neutral"),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to='uploads/')
    caption = models.TextField()
    sentiment = models.CharField(
        max_length=10, choices=SENTIMENT_CHOICES, default="Neutral"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.sentiment}"


class Comment(models.Model):
    post = models.ForeignKey('Post', related_name='comments', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on {self.post.caption}"
