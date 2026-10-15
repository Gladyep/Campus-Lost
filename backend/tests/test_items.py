from datetime import date
from io import BytesIO
from tempfile import TemporaryDirectory

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.test.utils import override_settings
from PIL import Image as PillowImage
from rest_framework.test import APIClient

from apps.items.models import Category, Item, ItemImage
from apps.matching.services import score_items

User = get_user_model()


class ItemApiTests(TestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner@example.edu', password='A-valid-pass-123', name='Owner')
        self.other = User.objects.create_user(email='other@example.edu', password='A-valid-pass-123', name='Other')
        self.category = Category.objects.create(name='Electronics')
        self.item = Item.objects.create(reporter=self.owner, category=self.category, title='Lost notebook', description='Blue cover and silver pen inside', item_type=Item.Type.LOST, location='North library', event_date=date(2026, 10, 10))
        self.client = APIClient()
        self.media_directory = TemporaryDirectory()
        media_settings = override_settings(MEDIA_ROOT=self.media_directory.name)
        media_settings.enable()
        self.addCleanup(self.media_directory.cleanup)
        self.addCleanup(media_settings.disable)

    @staticmethod
    def image_upload(name, color):
        image = PillowImage.new('RGB', (64, 64), color)
        content = BytesIO()
        image.save(content, format='PNG')
        return SimpleUploadedFile(name, content.getvalue(), content_type='image/png')

    def test_visual_search_ranks_matching_found_images_and_excludes_ineligible_items(self):
        found = Item.objects.create(reporter=self.owner, category=self.category, title='Blue found bag', description='Blue canvas bag', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10))
        ItemImage.objects.create(item=found, image=self.image_upload('found.png', (20, 80, 220)))
        closed = Item.objects.create(reporter=self.owner, category=self.category, title='Closed blue bag', description='Previously listed', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10), status=Item.Status.CLOSED)
        ItemImage.objects.create(item=closed, image=self.image_upload('closed.png', (20, 80, 220)))
        lost = Item.objects.create(reporter=self.owner, category=self.category, title='Lost blue bag', description='A lost report', item_type=Item.Type.LOST, location='North library', event_date=date(2026, 10, 10))
        ItemImage.objects.create(item=lost, image=self.image_upload('lost.png', (20, 80, 220)))
        self.client.force_authenticate(self.other)

        response = self.client.post('/api/visual-search/', {'image': self.image_upload('query.png', (20, 80, 220))}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], found.pk)
        self.assertEqual(response.data['results'][0]['similarity'], 100)
        self.assertNotIn('reporter_name', response.data['results'][0])
        self.assertNotIn('email', response.data['results'][0])

    def test_visual_search_applies_category_location_and_date_filters(self):
        found = Item.objects.create(reporter=self.owner, category=self.category, title='Blue found bag', description='Blue canvas bag', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10))
        ItemImage.objects.create(item=found, image=self.image_upload('north.png', (20, 80, 220)))
        other_category = Category.objects.create(name='Bags')
        other = Item.objects.create(reporter=self.owner, category=other_category, title='Blue bag elsewhere', description='Blue backpack', item_type=Item.Type.FOUND, location='South hall', event_date=date(2026, 10, 11))
        ItemImage.objects.create(item=other, image=self.image_upload('south.png', (20, 80, 220)))
        self.client.force_authenticate(self.other)

        response = self.client.post('/api/visual-search/', {
            'image': self.image_upload('query.png', (20, 80, 220)),
            'category': 'Electronics',
            'location': 'North',
            'event_date': '2026-10-10',
        }, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in response.data['results']], [found.pk])

    def test_visual_search_rejects_invalid_images_and_requires_authentication(self):
        self.client.force_authenticate(self.other)
        invalid = self.client.post('/api/visual-search/', {
            'image': SimpleUploadedFile('broken.png', b'not an image', content_type='image/png'),
        }, format='multipart')
        self.assertEqual(invalid.status_code, 400)
        self.assertIn('image', invalid.data)

        self.client.force_authenticate(user=None)
        unauthenticated = self.client.post('/api/visual-search/', {
            'image': self.image_upload('query.png', (20, 80, 220)),
        }, format='multipart')
        self.assertEqual(unauthenticated.status_code, 401)

    def test_report_owner_can_edit_but_other_user_cannot(self):
        self.client.force_authenticate(self.other)
        denied = self.client.patch(f'/api/items/{self.item.pk}/', {'title': 'Changed'}, format='json')
        self.assertEqual(denied.status_code, 403)
        self.client.force_authenticate(self.owner)
        allowed = self.client.patch(f'/api/items/{self.item.pk}/', {'title': 'Updated report'}, format='json')
        self.assertEqual(allowed.status_code, 200)

    def test_item_search_returns_matching_report(self):
        response = self.client.get('/api/items/?search=notebook')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)

    def test_matching_score_is_bounded_and_rewards_shared_details(self):
        other = Item(reporter=self.other, category=self.category, title='Blue notebook', description='Blue cover silver pen', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10))
        score = score_items(self.item, other)
        self.assertGreaterEqual(score, 80)
        self.assertLessEqual(score, 100)

    def test_registration_returns_a_token_and_public_profile(self):
        response = self.client.post('/api/auth/register/', {
            'name': 'New Student',
            'email': 'new.student@example.edu',
            'password': 'A-strong-password-42',
        }, format='json')
        self.assertEqual(response.status_code, 201)
        self.assertIn('access', response.data)
        self.assertNotIn('password', response.data['user'])

    def test_claim_is_unique_and_hidden_from_nonparticipants(self):
        found = Item.objects.create(reporter=self.owner, category=self.category, title='Found notebook', description='Blue notebook', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10))
        self.client.force_authenticate(self.other)
        submitted = self.client.post('/api/claims/', {'item': found.pk, 'evidence': 'There is a tiny star on the inside cover.'}, format='json')
        self.assertEqual(submitted.status_code, 201)
        self.assertEqual(submitted.data['status'], 'PENDING')
        duplicate = self.client.post('/api/claims/', {'item': found.pk, 'evidence': 'Second attempt'}, format='json')
        self.assertEqual(duplicate.status_code, 400)
        outsider = User.objects.create_user(email='outsider@example.edu', password='A-valid-pass-123', name='Outsider')
        self.client.force_authenticate(outsider)
        hidden = self.client.get(f"/api/claims/{submitted.data['id']}/")
        self.assertEqual(hidden.status_code, 404)

    def test_closed_reports_are_archived_not_deleted(self):
        self.client.force_authenticate(self.owner)
        closed = self.client.delete(f'/api/items/{self.item.pk}/')
        self.assertEqual(closed.status_code, 204)
        self.assertTrue(Item.objects.filter(pk=self.item.pk, status=Item.Status.CLOSED).exists())
        public_list = self.client.get('/api/items/')
        self.assertEqual(public_list.data['count'], 0)
        own_reports = self.client.get('/api/items/?mine=true')
        self.assertEqual(own_reports.data['count'], 1)