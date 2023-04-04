import shutil
import tempfile

from django.conf import settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Group, Post, User

TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='author')
        cls.group = Group.objects.create(
            description='Описание тестовой группы',
            slug='test_slug',
            title='Тестовая группа',
        )
        cls.post = Post.objects.create(
            author=cls.author,
            group=cls.group,
            text='Тестовый текст поста',
        )

    def setUp(self):
        self.guest_client = Client()
        self.client.force_login(self.author)

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def test_post_with_image(self):
        """При отправке поста с картинкой создаётся запись в БД."""
        post_count = Post.objects.count()
        small_gif = (
             b'\x47\x49\x46\x38\x39\x61\x02\x00'
             b'\x01\x00\x80\x00\x00\x00\x00\x00'
             b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
             b'\x00\x00\x00\x2C\x00\x00\x00\x00'
             b'\x02\x00\x01\x00\x00\x02\x02\x0C'
             b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif',
        )
        form_data = {
            'group': self.group.id,
            'text': 'Тестовый текст поста c картинкой',
            'image': uploaded,
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.latest('id'))

    def test_post_edit_form(self):
        """При отправке формы со страницы post_edit происходит изменение
        поста с post_id в БД."""
        post = Post.objects.create(
            author=self.author,
            group=self.group,
            text='Текст поста для редактирования.',
        )
        edited_group = Group.objects.create(
            description='Описание тестовой группы для редактирования поста',
            slug='test_edit_slug',
            title='Тестовая группа для редактирования поста',
        )
        form_data = {
            'group': edited_group.id,
            'text': 'Отредактированный текст поста.'
        }
        self.client.post(
            reverse('posts:post_edit', args=[post.id]),
            data=form_data,
            follow=True
        )
        edited_post = Post.objects.get(id=post.id)
        self.assertEqual(post.author, edited_post.author)
        self.assertEqual(form_data['group'], edited_post.group.id)
        self.assertEqual(form_data['text'], edited_post.text)

    def test_post_create_form(self):
        """При отправке формы со страницы create_post создается новая запись в
        БД."""
        post_count = Post.objects.count()
        group = Group.objects.create(
            description='Описание тестовой группы для создания поста',
            slug='test_create_slug',
            title='Тестовая группа для создания поста',
        )
        form_data = {
            'group': group.id,
            'text': 'Тестовый текст поста',
        }
        response = self.client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': self.author}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(Post.objects.latest('id'))

    def test_anonymous_create_post(self):
        """Не авторизованный пользователь не может создать пост"""
        post_count = Post.objects.count()
        form_data = {
            'text': 'Test text',
            'group': self.group.id,
        }
        self.guest_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        self.assertEqual(Post.objects.count(), post_count)
        self.assertFalse(
            Post.objects.filter(
                text=form_data['text'],
                group=form_data['group'],
            ).exists()
        )
