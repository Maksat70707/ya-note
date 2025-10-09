from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse
from pytils.translit import slugify

from notes.forms import WARNING
from notes.models import Note

User = get_user_model()


class TestNoteCreation(TestCase):
    NOTE_TITLE = 'Заметка'
    NOTE_TEXT = 'Просто текст'
    NOTE_SLUG = 'test_slug'

    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('notes:add')
        cls.user = User.objects.create(username='Test User')
        cls.auth_client = Client()
        cls.auth_client.force_login(cls.user)
        cls.form_data = {
            'title': cls.NOTE_TITLE,
            'text': cls.NOTE_TEXT,
            'author': cls.user,
            'slug': cls.NOTE_SLUG
        }

    def test_anonymous_user_cant_create_note(self):
        self.client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_can_create_note(self):
        self.auth_client.post(self.url, data=self.form_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

        note = Note.objects.get()
        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.slug, self.NOTE_SLUG)

    def test_for_unique_slug(self):
        self.auth_client.post(self.url, data=self.form_data)
        response = self.auth_client.post(self.url, data=self.form_data)
        form = response.context['form']
        self.assertFormError(
            form=form,
            field='slug',
            errors=f'{self.NOTE_SLUG}{WARNING}'
        )
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_for_no_slug(self):
        no_slug_data = {
            'title': self.NOTE_TITLE,
            'text': self.NOTE_TEXT,
            'slug': ''
        }

        self.auth_client.post(self.url, data=no_slug_data)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)
        note = Note.objects.get()

        expected_slug = slugify(self.NOTE_TITLE)

        self.assertEqual(note.title, self.NOTE_TITLE)
        self.assertEqual(note.text, self.NOTE_TEXT)
        self.assertEqual(note.author, self.user)
        self.assertEqual(note.slug, expected_slug)


class TestNoteEditDelete(TestCase):

    NOTE_TITLE = 'Original Title'
    NOTE_TEXT = 'Original Text'
    NOTE_SLUG = 'original_slug'

    NEW_NOTE_TITLE = 'Edited Title'
    NEW_NOTE_TEXT = 'Edited Text'
    NEW_NOTE_SLUG = 'edited_slug'

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='User A')
        cls.author_client = Client()
        cls.author_client.force_login(cls.author)

        cls.other = User.objects.create(username='User B')
        cls.other_client = Client()
        cls.other_client.force_login(cls.other)

        cls.note = Note.objects.create(
            title=cls.NOTE_TITLE,
            text=cls.NOTE_TEXT,
            author=cls.author,
            slug=cls.NOTE_SLUG
        )
        cls.edit_url = reverse(
            'notes:edit',
            kwargs={'slug': cls.note.slug}
        )
        cls.delete_url = reverse(
            'notes:delete',
            kwargs={'slug': cls.note.slug}
        )
        cls.success_url = reverse('notes:success')

        cls.edited_note_data = {
            'title': cls.NEW_NOTE_TITLE,
            'text': cls.NEW_NOTE_TEXT,
            'slug': cls.NEW_NOTE_SLUG
        }

    def test_author_can_delete_note(self):
        response = self.author_client.delete(self.delete_url)
        self.assertRedirects(response, self.success_url)
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 0)

    def test_user_cant_delete_note_of_another_user(self):
        response = self.other_client.delete(self.delete_url)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        notes_count = Note.objects.count()
        self.assertEqual(notes_count, 1)

    def test_author_can_edit_note(self):
        response = self.author_client.post(
            self.edit_url, data=self.edited_note_data)
        self.assertRedirects(response, self.success_url)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NEW_NOTE_TITLE)
        self.assertEqual(self.note.text, self.NEW_NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NEW_NOTE_SLUG)

    def test_user_cant_edit_note_of_another_user(self):
        response = self.other_client.post(
            self.edit_url, data=self.edited_note_data)
        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.note.refresh_from_db()
        self.assertEqual(self.note.title, self.NOTE_TITLE)
        self.assertEqual(self.note.text, self.NOTE_TEXT)
        self.assertEqual(self.note.slug, self.NOTE_SLUG)
