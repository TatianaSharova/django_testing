from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()

TEXT = 'Первоначальный текст'
TITLE = 'Заголовок'
SLUG = 'slug'


class TestNoteCreation(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create(username='Пользователь')
        cls.user_client = Client()
        cls.user_client.force_login(cls.user)
        cls.add_url = reverse('notes:add')
        cls.done_url = reverse('notes:success')
        cls.form_data = {'text': TEXT,
                         'title': TITLE,
                         'slug': SLUG,
                         'author': cls.user,
                         }

    def test_anonymous_cant_create_note(self):
        login_url = reverse('users:login')
        response = self.client.post(self.add_url, data=self.form_data)
        expected_url = f'{login_url}?next={self.add_url}'
        self.assertRedirects(response, expected_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        response = self.user_client.post(self.add_url, data=self.form_data)
        self.assertRedirects(response, self.done_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()
        self.assertEqual(note.text, TEXT)
        self.assertEqual(note.title, TITLE)
        self.assertEqual(note.slug, SLUG)
        self.assertEqual(note.author, self.user)

    def test_empty_slug(self):
        url = reverse('notes:add')
        self.form_data.pop('slug')
        response = self.user_client.post(url, data=self.form_data)
        self.assertRedirects(response, reverse('notes:success'))
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        new_note = Note.objects.get()
        expected_slug = slugify(self.form_data['title'])
        self.assertEqual(new_note.slug, expected_slug)


class TestNoteEditDelete(TestCase):

    NEW_TEXT = 'Обновлённый текст'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='Автор')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)
        cls.note = Note.objects.create(
            title=TITLE,
            text=TEXT,
            author=cls.author,
            slug=SLUG,
        )
        cls.add_url = reverse('notes:add')
        cls.edit_url = reverse('notes:edit', args=(cls.note.slug,))
        cls.delete_url = reverse('notes:delete', args=(cls.note.slug,))
        cls.done_url = reverse('notes:success')
        cls.form_data = {
            'text': cls.NEW_TEXT,
            'title': TITLE,
            'author': cls.author,
            'slug': SLUG,
        }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.done_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_anonymus_cant_delete_note(self):
        login_url = reverse('users:login')
        response = self.client.delete(self.delete_url)
        redirect_url = f'{login_url}?next={self.delete_url}'
        self.assertRedirects(response, redirect_url)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(self.edit_url, data=self.form_data)
        self.assertRedirects(response, self.done_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, self.NEW_TEXT)

    def test_anonymus_cant_edit_note(self):
        login_url = reverse('users:login')
        response = self.client.post(self.edit_url, data=self.form_data)
        redirect_url = f'{login_url}?next={self.edit_url}'
        self.assertRedirects(response, redirect_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.text, TEXT)

    def test_user_cant_use_used_slug(self):
        response = self.author_client.post(self.add_url, data=self.form_data)
        self.assertFormError(
            response,
            form='form',
            field='slug',
            errors=(self.note.slug + WARNING)
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
