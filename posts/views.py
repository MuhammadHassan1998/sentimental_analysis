from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView
from django.urls import reverse_lazy
from django.http import Http404
from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import FormMixin
from django.contrib.auth import login
from django.core.cache import cache
from .models import Post
from .forms import PostForm, CommentForm, RegisterForm, CustomLoginForm
from utils.sentiment_model import predict_sentiment

sentiment_map = {
    "Very Negative": 0,
    "Negative": 1,
    "Neutral": 2,
    "Positive": 3,
    "Very Positive": 4,
}


class PostFeedView(LoginRequiredMixin, FormMixin, ListView):
    template_name = "posts/home.html"
    form_class = PostForm
    success_url = reverse_lazy("home")
    model = Post
    context_object_name = "posts"
    ordering = ["-created_at"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = self.get_form()
        context["comment_form"] = CommentForm()
        return context

    def get_queryset(self):
        queryset = cache.get("post_feed")
        if queryset is None:
            print("⏳ Cache miss: Fetching posts from DB and saving to Redis...")
            queryset = (
                Post.objects.select_related("user")
                .prefetch_related("comments")
                .order_by("-created_at")
            )
            cache.set("post_feed", queryset, timeout=60)  # Cache for 60 seconds
            print("✅ Post feed cached in Redis.")
        else:
            print("✅ Cache hit: Loaded posts from Redis.")
        return queryset

    def post(self, request, *args, **kwargs):
        if "caption" in request.POST:
            form = self.get_form()
            if form.is_valid():
                response = self.form_valid(form)
                cache.delete("post_feed")
                return response
            else:
                return self.form_invalid(form)

        elif "text" in request.POST:
            # Comment submission
            comment_form = CommentForm(request.POST)
            if comment_form.is_valid():
                post_id = request.POST.get("post_id")
                comment = comment_form.save(commit=False)
                comment.user = request.user
                comment.post_id = post_id

                # Predict and assign sentiment
                sentiment_score = predict_sentiment(comment.text)
                comment.sentiment = sentiment_map[sentiment_score]
                comment.save()
                cache.delete("post_feed")

                # Recalculate average sentiment for the post
                post = Post.objects.get(id=post_id)
                comment_sentiments = post.comments.values_list("sentiment", flat=True)

                if comment_sentiments:
                    avg_sentiment = round(
                        sum(comment_sentiments) / len(comment_sentiments)
                    )
                    post.sentiment = avg_sentiment
                    post.save()

                return redirect("home")

        return redirect("home")

    def form_valid(self, form):
        post = form.save(commit=False)
        post.user = self.request.user
        post.save()
        return super().form_valid(form)


class DeletePostView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        post = get_object_or_404(Post, id=post_id)

        if post.user != request.user:
            raise Http404("You are not authorized to delete this post.")

        post.delete()

        # Clear Redis cache so home page reflects the change
        cache.delete("post_feed")
        print("Deleted post_feed cache after post deletion.")

        return redirect("home")


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)


class CustomLoginView(LoginView):
    form_class = CustomLoginForm
    template_name = "registration/login.html"
