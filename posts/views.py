from django.views.generic import ListView, CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.http import Http404
from django.views.generic import View
from django.shortcuts import get_object_or_404, redirect
from django.views.generic.edit import FormMixin
from django.contrib.auth import login
from .models import Post
from .forms import PostForm, CommentForm, RegisterForm


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

    def post(self, request, *args, **kwargs):
        if "caption" in request.POST:
            # Post creation
            form = self.get_form()
            if form.is_valid():
                return self.form_valid(form)
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
                comment.save()
                return redirect("home")

        return redirect("home")

    def form_valid(self, form):
        post = form.save(commit=False)
        post.user = self.request.user
        post.save()
        return super().form_valid(form)


class DeletePostView(LoginRequiredMixin, View):
    def post(self, request, post_id):
        # Get the post object or raise a 404 if not found
        post = get_object_or_404(Post, id=post_id)

        # Check if the logged-in user is the one who created the post
        if post.user != request.user:
            raise Http404("You are not authorized to delete this post.")

        # If the user is the creator, delete the post
        post.delete()

        # Redirect to the homepage
        return redirect("home")


class RegisterView(CreateView):
    template_name = "registration/register.html"
    form_class = RegisterForm
    success_url = reverse_lazy("home")

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)
