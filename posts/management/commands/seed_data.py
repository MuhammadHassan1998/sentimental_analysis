import random
import os
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.conf import settings
from faker import Faker
from PIL import Image

from posts.models import Post, Comment
from .comments import MEANINGFUL_COMMENTS
from utils.sentiment_model import predict_sentiment

fake = Faker()

SENTIMENT_CHOICES = [0, 1, 2, 3, 4]

sentiment_map = {
    "Very Negative": 0,
    "Negative": 1,
    "Neutral": 2,
    "Positive": 3,
    "Very Positive": 4,
}


IMAGE_DIR = "sample_images"


def create_realistic_image():
    available_images = [
        f
        for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ]
    if not available_images:
        raise Exception("No images found in sample_images/")

    chosen_file = random.choice(available_images)
    full_path = os.path.join(IMAGE_DIR, chosen_file)

    with open(full_path, "rb") as f:
        return SimpleUploadedFile(
            name=chosen_file,
            content=f.read(),
            content_type="image/jpeg",
        )


class Command(BaseCommand):
    help = "Seed the database with dummy users, posts, and comments"

    def add_arguments(self, parser):
        parser.add_argument("--users", type=int, default=5)
        parser.add_argument("--posts", type=int, default=20)
        parser.add_argument("--comments", type=int, default=50)

    def handle(self, *args, **kwargs):
        user_count = kwargs["users"]
        post_count = kwargs["posts"]
        comment_count = kwargs["comments"]

        self.stdout.write(self.style.SUCCESS(f"Creating {user_count} users..."))
        users = []
        for _ in range(user_count):
            username = fake.unique.user_name()
            email = fake.email()
            user = User.objects.create_user(
                username=username, email=email, password="password123"
            )
            users.append(user)

        self.stdout.write(self.style.SUCCESS(f"Creating {post_count} posts..."))
        posts = []
        for _ in range(post_count):
            user = random.choice(users)
            image = create_realistic_image()
            caption = fake.sentence(nb_words=10)
            sentiment = random.choice(SENTIMENT_CHOICES)
            post = Post.objects.create(
                user=user, image=image, caption=caption, sentiment=sentiment
            )
            posts.append(post)

        self.stdout.write(self.style.SUCCESS(f"Creating {comment_count} comments..."))
        for _ in range(comment_count):
            post = random.choice(posts)
            user = random.choice([u for u in users if u != post.user])

            # Select a random realistic comment
            all_texts = sum(MEANINGFUL_COMMENTS.values(), [])
            text = random.choice(all_texts)

            # Predict sentiment
            predicted_label = predict_sentiment(text)
            sentiment = sentiment_map[predicted_label]

            # Save comment with sentiment
            Comment.objects.create(post=post, user=user, text=text, sentiment=sentiment)

        # Now updating the posts according to the sentiments
        self.stdout.write(self.style.SUCCESS("Updating posts based on the comments."))
        for post in posts:
            comment_sentiments = post.comments.values_list("sentiment", flat=True)
            if comment_sentiments:
                avg_sentiment = round(sum(comment_sentiments) / len(comment_sentiments))
                post.sentiment = avg_sentiment
                post.save()

        self.stdout.write(self.style.SUCCESS("Seeding completed successfully."))
