from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from django.urls import reverse

from notes.forms import NoteForm
from notes.models import Note

User = get_user_model()


class TestList(TestCase):
    LIST_URL = reverse('notes:list')

    @classmethod
    def setUpTestData(cls):
        cls.author = User.objects.create(username='User A')
        cls.auth_client = Client()
        all_notes = [
            Note(
                title=f'Заметка {index}',
                text='Просто текст.',
                author=cls.author,
                slug=f'cucucu{index}'
            )
            for index in range(5)
        ]
        Note.objects.bulk_create(all_notes)

    def test_authorized_client_has_form(self):
        self.client.force_login(self.author)
        response = self.client.get(reverse('notes:add'))
        self.assertIn('form', response.context)
        self.assertIsInstance(response.context['form'], NoteForm)

    def test_notes_order(self):
        self.client.force_login(self.author)
        response = self.client.get(self.LIST_URL)
        object_list = response.context['object_list']
        all_ids = [notes.id for notes in object_list]
        sorted_ids = sorted(all_ids)
        self.assertEqual(all_ids, sorted_ids)

    def test_note_in_list_for_author(self):
        self.auth_client.force_login(self.author)
        response = self.auth_client.get(self.LIST_URL)
        object_list = response.context['object_list']
        notes = Note.objects.all()
        self.assertEqual(set(object_list), set(notes))

    def test_note_not_in_list_for_another_user(self):
        other_user = User.objects.create(username='User B')
        self.auth_client.force_login(other_user)
        response = self.auth_client.get(self.LIST_URL)
        object_list = response.context['object_list']
        self.assertEqual(len(object_list), 0)