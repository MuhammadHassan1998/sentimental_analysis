import random
import os
from io import BytesIO
from django.core.management.base import BaseCommand
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth.models import User
from django.conf import settings
from faker import Faker
from PIL import Image
import csv
import requests

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


CSV_PATH = "Appliances.csv"


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

        # Creating Users
        self.stdout.write(self.style.SUCCESS(f"Creating {user_count} users..."))
        users = []
        for _ in range(user_count):
            username = fake.unique.user_name()
            email = fake.email()
            user = User.objects.create_user(
                username=username, email=email, password="password123"
            )
            users.append(user)

        # Creating Posts
        self.stdout.write(self.style.SUCCESS("Creating posts from CSV..."))
        posts = []
        post_created = 0
        try:
            with open(CSV_PATH, newline="", encoding="utf-8") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    if post_created >= post_count:
                        break
                    image_url = row["image"].strip()
                    caption = row["name"].strip()
                    if not image_url:
                        continue
                    try:
                        response = requests.get(image_url, timeout=10)
                        if response.status_code != 200 or not response.content:
                            continue

                        img_name = os.path.basename(image_url.split("?")[0])
                        image_file = SimpleUploadedFile(
                            name=img_name,
                            content=response.content,
                            content_type="image/jpeg",
                        )

                        user = random.choice(users)
                        sentiment = random.choice(SENTIMENT_CHOICES)
                        post = Post.objects.create(
                            user=user,
                            image=image_file,
                            caption=caption,
                            sentiment=sentiment,
                        )
                        posts.append(post)
                        post_created += 1
                        if post_created % 10 == 0:
                            self.stdout.write(
                                self.style.SUCCESS(
                                    f"Number of posts created : {post_created}"
                                )
                            )
                    except Exception as e:
                        self.stdout.write(
                            self.style.WARNING(
                                f"Failed to create post for {caption}: {e}"
                            )
                        )

        except FileNotFoundError:
            self.stdout.write(self.style.ERROR(f"CSV file not found at {CSV_PATH}"))

        # Creating Comments
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
