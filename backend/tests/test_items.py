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
from apps.communication.models import Conversation, Notification

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
        recovered = Item.objects.create(reporter=self.owner, category=self.category, title='Recovered blue bag', description='Already reunited', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10), status=Item.Status.RECOVERED)
        ItemImage.objects.create(item=recovered, image=self.image_upload('recovered.png', (20, 80, 220)))
        lost = Item.objects.create(reporter=self.owner, category=self.category, title='Lost blue bag', description='A lost report', item_type=Item.Type.LOST, location='North library', event_date=date(2026, 10, 10))
        ItemImage.objects.create(item=lost, image=self.image_upload('lost.png', (20, 80, 220)))
        self.client.force_authenticate(self.other)

        response = self.client.post('/api/visual-search/', {'image': self.image_upload('query.png', (20, 80, 220))}, format='multipart')

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], found.pk)
        self.assertEqual(response.data['results'][0]['reporter_id'], self.owner.pk)
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
        self.assertEqual(response.data['results'][0]['reporter_id'], self.owner.pk)
        self.assertFalse(response.data['results'][0]['is_reporter'])

        self.client.force_authenticate(self.owner)
        owner_response = self.client.get('/api/items/?search=notebook')
        self.assertTrue(owner_response.data['results'][0]['is_reporter'])
        self.client.force_authenticate(self.other)
        other_response = self.client.get('/api/items/?search=notebook')
        self.assertFalse(other_response.data['results'][0]['is_reporter'])

    def test_search_item_reports_filters_type_and_item_date(self):
        found = Item.objects.create(reporter=self.owner, category=self.category, title='Blue headphones', description='Blue wireless headphones', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 12))
        lost = Item.objects.create(reporter=self.other, category=self.category, title='Lost headphones', description='Blue headphones', item_type=Item.Type.LOST, location='North library', event_date=date(2026, 10, 12))
        Item.objects.create(reporter=self.owner, category=self.category, title='Recovered headphones', description='Blue headphones', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 12), status=Item.Status.RECOVERED)

        response = self.client.get('/api/items/search-found/', {
            'q': '  BLUE headphone  ',
            'category': self.category.pk,
            'location': ' north ',
            'start_date': '2026-10-10',
            'end_date': '2026-10-13',
            'type': 'FOUND',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual([row['id'] for row in response.json()], [found.pk])
        lost_response = self.client.get('/api/items/search-found/', {
            'q': 'headphones',
            'category': self.category.name,
            'type': 'lost',
        })
        self.assertEqual([row['id'] for row in lost_response.json()], [lost.pk])

    def test_search_item_reports_matches_keywords_across_fields_and_both_types_by_default(self):
        bags = Category.objects.create(name='Bags')
        lost = Item.objects.create(
            reporter=self.owner,
            category=bags,
            title='a wildcraft bag',
            description='A blue bag left near the lab.',
            item_type=Item.Type.LOST,
            location='First floor, in front of the lab',
            event_date=date(2026, 10, 12),
        )
        found = Item.objects.create(
            reporter=self.other,
            category=bags,
            title='Blue travel bag',
            description='Wildcraft brand backpack',
            item_type=Item.Type.FOUND,
            location='First floor',
            event_date=date(2026, 10, 12),
        )

        response = self.client.get('/api/items/search-found/', {
            'q': '  blue   wildcraft ',
            'category': bags.pk,
            'location': ' FIRST FLOOR ',
            'start_date': '2026-10-12',
            'end_date': '2026-10-12',
        })

        self.assertEqual(response.status_code, 200)
        self.assertEqual({row['id'] for row in response.json()}, {lost.pk, found.pk})
        self.assertEqual({row['item_type'] for row in response.json()}, {Item.Type.LOST, Item.Type.FOUND})

        exact_report = self.client.get('/api/items/search-found/', {
            'q': ' a wildcraft bag ',
            'category': 'Bags',
            'type': 'LOST',
            'start_date': '2026-10-12',
            'end_date': '2026-10-12',
        })
        self.assertEqual([row['id'] for row in exact_report.json()], [lost.pk])

    def test_search_item_reports_rejects_unknown_report_type(self):
        response = self.client.get('/api/items/search-found/?type=CLAIMED')
        self.assertEqual(response.status_code, 400)
        self.assertIn('type', response.json())

    def test_search_found_rejects_invalid_date_ranges(self):
        response = self.client.get('/api/items/search-found/?start_date=2026-10-20&end_date=2026-10-10')
        self.assertEqual(response.status_code, 400)
        self.assertIn('end_date', response.json())

    def test_new_report_creates_notifications_for_other_users(self):
        self.client.force_authenticate(self.owner)

        response = self.client.post('/api/items/', {
            'category': self.category.name,
            'title': 'Lost blue bottle',
            'description': 'A blue bottle by the main hall.',
            'item_type': Item.Type.LOST,
            'location': 'Main hall',
            'event_date': '2026-10-12',
        }, format='json')

        self.assertEqual(response.status_code, 201)
        report_notice = Notification.objects.get(user=self.other, item_id=response.data['id'], kind=Notification.Kind.REPORT)
        self.assertEqual(report_notice.title, 'New lost-item report')
        self.assertIn('Electronics', report_notice.message)
        self.assertIn('Main hall', report_notice.message)
        self.assertIn('Oct 12, 2026', report_notice.message)
        self.assertFalse(Notification.objects.filter(user=self.owner, item_id=response.data['id']).exists())
        self.client.force_authenticate(self.other)
        alerts = self.client.get('/api/notifications/')
        self.assertEqual(alerts.status_code, 200)
        self.assertEqual(alerts.data['results'][0]['item_status'], Item.Status.OPEN)
        from apps.communication.services import notify_new_report

        notify_new_report(Item.objects.get(pk=response.data['id']))
        self.assertEqual(Notification.objects.filter(user=self.other, item_id=response.data['id'], kind=Notification.Kind.REPORT).count(), 1)

    def test_matching_found_report_notifies_lost_report_owner(self):
        self.client.force_authenticate(self.other)

        response = self.client.post('/api/items/', {
            'category': self.category.name,
            'title': 'Found blue notebook',
            'description': self.item.description,
            'item_type': Item.Type.FOUND,
            'location': self.item.location,
            'event_date': self.item.event_date.isoformat(),
        }, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertTrue(Notification.objects.filter(user=self.owner, item_id=response.data['id'], kind=Notification.Kind.REPORT).exists())
        self.assertTrue(Notification.objects.filter(user=self.owner, match__found_item_id=response.data['id'], kind=Notification.Kind.MATCH).exists())
        self.assertTrue(Notification.objects.filter(user=self.other, match__found_item_id=response.data['id'], kind=Notification.Kind.MATCH).exists())
        self.assertFalse(Notification.objects.filter(user=self.other, item_id=response.data['id'], kind=Notification.Kind.REPORT).exists())
        found_notice = Notification.objects.get(user=self.owner, item_id=response.data['id'], kind=Notification.Kind.REPORT)
        self.assertIn(self.category.name, found_notice.message)
        self.assertIn(self.item.location, found_notice.message)
        self.assertIn('Oct 10, 2026', found_notice.message)
        from apps.matching.services import evaluate_matches

        evaluate_matches(Item.objects.get(pk=response.data['id']))
        self.assertEqual(Notification.objects.filter(match__found_item_id=response.data['id'], kind=Notification.Kind.MATCH).count(), 2)

    def test_item_report_rejects_a_future_event_date(self):
        self.client.force_authenticate(self.owner)

        response = self.client.post('/api/items/', {
            'category': self.category.name,
            'title': 'Found blue bottle',
            'description': 'A blue bottle by the main hall.',
            'item_type': Item.Type.FOUND,
            'location': 'Main hall',
            'event_date': '2999-01-01',
        }, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('event_date', response.data)

    def test_item_report_accepts_iso_date_from_multipart_form(self):
        self.client.force_authenticate(self.owner)
        selected_date = '2026-10-19'

        response = self.client.post('/api/items/', {
            'category': self.category.name,
            'title': 'Found blue bottle',
            'description': 'A blue bottle by the main hall.',
            'item_type': Item.Type.FOUND,
            'location': 'Main hall',
            'event_date': selected_date,
        }, format='multipart')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['event_date'], selected_date)
        self.assertEqual(Item.objects.get(pk=response.data['id']).event_date.isoformat(), selected_date)

    def test_contact_reporter_reuses_private_conversation_and_notifies_recipient(self):
        found = Item.objects.create(reporter=self.owner, category=self.category, title='Found blue headphones', description='Blue headphones by the library.', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 12))
        self.client.force_authenticate(self.other)

        first = self.client.post('/api/conversations/', {'item': found.pk}, format='json')
        second = self.client.post('/api/conversations/', {'item': found.pk}, format='json')

        self.assertEqual(first.status_code, 201)
        self.assertEqual(second.data['id'], first.data['id'])
        conversation = Conversation.objects.get(pk=first.data['id'])
        self.assertIsNone(conversation.claim_id)
        self.assertSetEqual(set(conversation.participants.values_list('pk', flat=True)), {self.owner.pk, self.other.pk})

        sent = self.client.post(f"/api/conversations/{conversation.pk}/messages/", {'message_text': 'I think this may be mine.'}, format='json')

        self.assertEqual(sent.status_code, 201)
        notification = Notification.objects.get(user=self.owner, kind=Notification.Kind.MESSAGE)
        self.assertEqual(notification.conversation_id, conversation.pk)
        self.assertIn('Found blue headphones', notification.title)
        self.assertNotIn('I think this may be mine.', notification.message)

        outsider = User.objects.create_user(email='outsider@example.edu', password='A-valid-pass-123', name='Outsider')
        self.client.force_authenticate(outsider)
        denied = self.client.get(f'/api/conversations/{conversation.pk}/messages/')
        self.assertEqual(denied.status_code, 404)

    def test_recovery_notifies_the_other_conversation_participant(self):
        found = Item.objects.create(reporter=self.owner, category=self.category, title='Found blue headphones', description='Blue headphones by the library.', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 12))
        self.client.force_authenticate(self.other)
        conversation = self.client.post('/api/conversations/', {'item': found.pk}, format='json')
        self.client.force_authenticate(self.owner)

        recovered = self.client.post(f'/api/items/{found.pk}/recover/')

        self.assertEqual(recovered.status_code, 200)
        self.assertTrue(Notification.objects.filter(user=self.other, item=found, kind=Notification.Kind.STATUS).exists())

    def test_notification_management_is_scoped_to_the_recipient(self):
        first = Notification.objects.create(user=self.owner, kind=Notification.Kind.REPORT, title='New lost report', message='A lost item was reported.', item=self.item)
        second = Notification.objects.create(user=self.owner, kind=Notification.Kind.CLAIM, title='Claim received', message='A claim was submitted.', item=self.item)
        foreign = Notification.objects.create(user=self.other, kind=Notification.Kind.MESSAGE, title='New message', message='A message arrived.', item=self.item)
        self.client.force_authenticate(self.owner)

        unread = self.client.get('/api/notifications/unread-count/')
        listing = self.client.get('/api/notifications/?category=claims')
        self.assertEqual(unread.data['count'], 2)
        self.assertEqual(listing.data['count'], 1)
        self.assertEqual(listing.data['results'][0]['title'], 'Claim received')

        read_all = self.client.patch('/api/notifications/read-all/', {}, format='json')
        self.assertEqual(read_all.data, {'updated': 2, 'unread_count': 0})
        self.assertEqual(self.client.get('/api/notifications/unread-count/').data['count'], 0)

        mark_one = self.client.patch(f'/api/notifications/{first.pk}/read/', {}, format='json')
        self.assertEqual(mark_one.status_code, 200)
        deleted = self.client.delete(f'/api/notifications/{first.pk}/')
        self.assertEqual(deleted.status_code, 204)
        cleared = self.client.delete('/api/notifications/clear-read/')
        self.assertEqual(cleared.data['deleted'], 1)

        self.client.force_authenticate(self.other)
        forbidden = self.client.patch(f'/api/notifications/{second.pk}/read/', {}, format='json')
        self.assertEqual(forbidden.status_code, 404)
        self.assertTrue(Notification.objects.filter(pk=foreign.pk, user=self.other).exists())

    def test_moderation_notifications_reach_admin_and_reporter_without_private_notes(self):
        administrator = User.objects.create_user(
            email='admin@example.edu', password='A-valid-pass-123', name='Admin', is_staff=True,
        )
        self.client.force_authenticate(self.other)
        submitted = self.client.post('/api/reports/', {
            'item': self.item.pk,
            'reason': 'This listing may be suspicious.',
        }, format='json')

        self.assertEqual(submitted.status_code, 201)
        admin_notice = Notification.objects.get(user=administrator, moderation_report_id=submitted.data['id'])
        self.assertEqual(admin_notice.kind, Notification.Kind.MODERATION)
        self.client.force_authenticate(administrator)
        decision = self.client.post(f"/api/admin/reports/{submitted.data['id']}/decision/", {
            'status': 'RESOLVED',
            'reason': 'private moderation note',
        }, format='json')

        self.assertEqual(decision.status_code, 200)
        reporter_notice = Notification.objects.get(user=self.other, moderation_report_id=submitted.data['id'])
        self.assertIn('resolved', reporter_notice.message.lower())
        self.assertNotIn('private moderation note', reporter_notice.message)

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
        self.assertTrue(Notification.objects.filter(user=self.owner, claim_id=submitted.data['id'], kind=Notification.Kind.CLAIM).exists())
        self.client.force_authenticate(self.owner)
        self_claim = self.client.post('/api/claims/', {'item': found.pk, 'evidence': 'I reported this item.'}, format='json')
        self.assertEqual(self_claim.status_code, 400)
        request_info = self.client.patch(f"/api/claims/{submitted.data['id']}/decision/", {'status': 'UNDER_VERIFICATION'}, format='json')
        self.assertEqual(request_info.status_code, 200)
        self.assertTrue(Notification.objects.filter(user=self.other, claim_id=submitted.data['id'], title='More verification information requested').exists())
        decision = self.client.patch(f"/api/claims/{submitted.data['id']}/decision/", {'status': 'REJECTED'}, format='json')
        self.assertEqual(decision.status_code, 200)
        self.assertTrue(Notification.objects.filter(user=self.other, claim_id=submitted.data['id'], kind=Notification.Kind.CLAIM).exists())
        self.client.force_authenticate(self.other)
        duplicate = self.client.post('/api/claims/', {'item': found.pk, 'evidence': 'Second attempt'}, format='json')
        self.assertEqual(duplicate.status_code, 400)
        outsider = User.objects.create_user(email='outsider@example.edu', password='A-valid-pass-123', name='Outsider')
        self.client.force_authenticate(outsider)
        hidden = self.client.get(f"/api/claims/{submitted.data['id']}/")
        self.assertEqual(hidden.status_code, 404)

    def test_requested_verification_updates_item_and_notifies_owner_of_answers(self):
        from apps.claims.models import VerificationQuestion

        found = Item.objects.create(reporter=self.owner, category=self.category, title='Found notebook', description='Blue notebook', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10))
        question = VerificationQuestion.objects.create(item=found, question_text='What is one mark on the item?')
        self.client.force_authenticate(self.other)
        submitted = self.client.post('/api/claims/', {
            'item': found.pk,
            'evidence': 'I can identify the item.',
        }, format='json')
        self.assertEqual(submitted.status_code, 201)

        self.client.force_authenticate(self.owner)
        requested = self.client.patch(
            f"/api/claims/{submitted.data['id']}/decision/",
            {'status': 'UNDER_VERIFICATION'},
            format='json',
        )
        self.assertEqual(requested.status_code, 200)
        found.refresh_from_db()
        self.assertEqual(found.status, Item.Status.UNDER_VERIFICATION)
        self.assertTrue(Notification.objects.filter(
            user=self.other,
            claim_id=submitted.data['id'],
            title='More verification information requested',
        ).exists())

        self.client.force_authenticate(self.other)
        answers = self.client.post(
            f"/api/claims/{submitted.data['id']}/answers/",
            {'answers': [{'question': question.pk, 'answer_text': 'A small star on the cover.'}]},
            format='json',
        )
        self.assertEqual(answers.status_code, 201)
        owner_notice = Notification.objects.get(
            user=self.owner,
            claim_id=submitted.data['id'],
            title='Verification information received',
        )
        self.assertNotIn('small star', owner_notice.message)
    def test_owner_delete_removes_report_and_archived_lists_no_longer_include_it(self):
        self.client.force_authenticate(self.owner)
        deleted = self.client.delete(f'/api/items/{self.item.pk}/')
        self.assertEqual(deleted.status_code, 204)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())
        public_list = self.client.get('/api/items/')
        self.assertEqual(public_list.data['count'], 0)
        own_reports = self.client.get('/api/items/?mine=true')
        self.assertEqual(own_reports.data['count'], 0)

    def test_non_owner_cannot_delete_another_users_report(self):
        self.client.force_authenticate(self.other)

        response = self.client.delete(f'/api/items/{self.item.pk}/')

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_owner_can_delete_an_archived_report(self):
        self.item.status = Item.Status.RECOVERED
        self.item.save(update_fields=('status',))
        self.client.force_authenticate(self.owner)

        response = self.client.delete(f'/api/items/{self.item.pk}/')

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Item.objects.filter(pk=self.item.pk).exists())

    def test_unauthenticated_user_cannot_delete_report(self):
        response = self.client.delete(f'/api/items/{self.item.pk}/')

        self.assertIn(response.status_code, (401, 403))
        self.assertTrue(Item.objects.filter(pk=self.item.pk).exists())

    def test_report_with_claim_history_cannot_be_hard_deleted(self):
        found = Item.objects.create(reporter=self.owner, category=self.category, title='Found notebook', description='Blue notebook', item_type=Item.Type.FOUND, location='North library', event_date=date(2026, 10, 10))
        self.client.force_authenticate(self.other)
        claim = self.client.post('/api/claims/', {'item': found.pk, 'evidence': 'There is a small mark inside.'}, format='json')
        self.assertEqual(claim.status_code, 201)
        self.client.force_authenticate(self.owner)

        response = self.client.delete(f'/api/items/{found.pk}/')

        self.assertEqual(response.status_code, 409)
        self.assertTrue(Item.objects.filter(pk=found.pk).exists())