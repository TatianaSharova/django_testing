from http import HTTPStatus

from django.test import TestCase
from django.urls import reverse

from .test_logic import AUTHOR, SLUG, TEXT, TITLE, USER
from notes.models import Note, User


class TestRoutes(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username=AUTHOR)
        cls.reader = User.objects.create(username=USER)
        cls.note = Note.objects.create(
            title=TITLE,
            text=TEXT,
            author=cls.author,
            slug=SLUG,
        )

    def test_pages_availability(self):
        """
        Главная страница и страницы регистрации пользователей, входа в

        учётную запись и выхода из неё доступны анонимным пользователям.
        """
        for name in (
            ('notes:home'),
            ('users:login'),
            ('users:logout'),
            ('users:signup'),
        ):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_availability_for_detail_note_edit_and_delete(self):
        """
        Страницы отдельной заметки, удаления и редактирования заметки

        доступны только автору заметки. Если на эти страницы попытается

        зайти другой пользователь — вернётся ошибка 404.
        """
        users_statuses = (
            (self.author, HTTPStatus.OK),
            (self.reader, HTTPStatus.NOT_FOUND),
        )
        for user, status in users_statuses:
            self.client.force_login(user)
            for name in ('notes:edit',
                         'notes:delete',
                         'notes:detail',
                         ):
                with self.subTest(user=user, name=name):
                    url = reverse(name, args=(self.note.slug,))
                    response = self.client.get(url)
                    self.assertEqual(response.status_code, status)

    def test_pages_availability_for_auth_user(self):
        """
        Аутентифицированному пользователю доступна страница со списком

        заметок, страница успешного добавления заметки,

        страница добавления новой заметки.
        """
        self.client.force_login(self.author)
        for name in ('notes:add',
                     'notes:success',
                     'notes:list',
                     ):
            with self.subTest(name=name):
                url = reverse(name)
                response = self.client.get(url)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_for_anonymous_client(self):
        """
        При попытке перейти на страницу списка заметок,

        страницу успешного добавления записи, страницу добавления заметки,

        отдельной заметки, редактирования или удаления заметки

        анонимный пользователь перенаправляется на страницу логина.
        """
        login_url = reverse('users:login')
        urls = (
            ('notes:detail', (self.note.slug,)),
            ('notes:edit', (self.note.slug,)),
            ('notes:delete', (self.note.slug,)),
            ('notes:add', None),
            ('notes:success', None),
            ('notes:list', None),
        )
        for name, arg in urls:
            if arg is None:
                with self.subTest(name=name):
                    url = reverse(name)
                    redirect_url = f'{login_url}?next={url}'
                    response = self.client.get(url)
                    self.assertRedirects(response, redirect_url)
            else:
                with self.subTest(name=name, arg=arg):
                    url = reverse(name, args=arg)
                    redirect_url = f'{login_url}?next={url}'
                    response = self.client.get(url)
                    self.assertRedirects(response, redirect_url)
