from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from .forms import PostForm, CommentForm
from .models import Group, Post, User, Comment, Follow


def index(request):
    """Главная страница с записями."""
    posts_list = Post.objects.all()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/index.html', context)


def group_posts(request, slug):
    """Страница сообщества."""
    group = get_object_or_404(Group, slug=slug)
    posts_list = group.posts.all()
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'group': group,
        'page_obj': page_obj,
    }
    return render(request, 'posts/group_list.html', context)


def profile(request, username):
    """Страница профиля."""
    author = get_object_or_404(User, username=username)
    post_list = author.posts.select_related('group')
    count = post_list.count()
    following = Follow.objects.filter(user=request.user.id, author=author)
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'count': count,
        'author': author,
        'post_list': post_list,
        'page_obj': page_obj,
        'following': following,
    }
    return render(request, 'posts/profile.html', context)


def post_detail(request, post_id):
    """Страница поста."""
    one_post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    comment = Comment.objects.filter(post=post_id)
    context = {
        'one_post': one_post,
        'form': form,
        'comment': comment,
    }
    return render(request, 'posts/post_detail.html', context)


@login_required
def post_create(request):
    """Создание поста."""
    form = PostForm(
        request.POST or None,
        files=request.FILES or None,
    )
    if form.is_valid():
        post = form.save(commit=False)
        post.author_id = request.user.id
        form.save()
        return redirect('posts:profile', request.user.username)
    form = PostForm()
    return render(request, 'posts/create_post.html', {'form': form})


@login_required
def post_edit(request, post_id):
    """Редактирование поста."""
    object_post = get_object_or_404(Post, id=post_id)
    if object_post.author == request.user:
        form = PostForm(
            request.POST or None,
            files=request.FILES or None,
            instance=object_post
        )
        context = {
            'is_edit': True,
            'form': form
        }
        if form.is_valid():
            form.save()
            return redirect('posts:post_detail', post_id=post_id)
        return render(request, 'posts/create_post.html', context)
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def add_comment(request, post_id):
    """Добавление комментария."""
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)
    if form.is_valid():
        comment = form.save(commit=False)
        comment.author = request.user
        comment.post = post
        comment.save()
    return redirect('posts:post_detail', post_id=post_id)


@login_required
def follow_index(request):
    """Страница с подписками."""
    posts_list = Post.objects.select_related('author', 'group').filter(
        author__following__user=request.user)
    paginator = Paginator(posts_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'page_obj': page_obj,
    }
    return render(request, 'posts/follow.html', context)


@login_required
def profile_follow(request, username):
    """Подписка на автора."""
    following = get_object_or_404(User, username=username)
    follower = request.user
    if follower != following and follower != following.follower:
        Follow.objects.get_or_create(user=follower, author=following)
    return redirect('posts:profile', username)


@login_required
def profile_unfollow(request, username):
    """Отписка от автора."""
    Follow.objects.filter(
        user=request.user,
        author__username=username
    ).delete()
    return redirect('posts:profile', username)
