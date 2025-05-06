from django.db import models
from django.contrib.auth.models import User


class Post(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    image = models.ImageField(upload_to="uploads/")
    caption = models.TextField()
    sentiment = models.IntegerField(
        choices=[
            (i, label)
            for i, label in {
                0: "Very Negative",
                1: "Negative",
                2: "Neutral",
                3: "Positive",
                4: "Very Positive",
            }.items()
        ],
        default=2,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.sentiment}"


class Comment(models.Model):
    post = models.ForeignKey("Post", related_name="comments", on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    text = models.TextField()
    sentiment = models.IntegerField(
        choices=[
            (i, label)
            for i, label in {
                0: "Very Negative",
                1: "Negative",
                2: "Neutral",
                3: "Positive",
                4: "Very Positive",
            }.items()
        ],
        default=2,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} on {self.post.caption}"
