from rest_framework import serializers

from .models import Conversation, Message, Notification


class NotificationSerializer(serializers.ModelSerializer):
    title = serializers.SerializerMethodField()
    item_title = serializers.CharField(source='item.title', read_only=True, default='')
    item_status = serializers.CharField(source='item.status', read_only=True, default='')
    claim_status = serializers.CharField(source='claim.status', read_only=True, default='')
    claim_item = serializers.IntegerField(source='claim.item_id', read_only=True, default=None)
    claim_item_title = serializers.CharField(source='claim.item.title', read_only=True, default='')

    class Meta:
        model = Notification
        fields = ('id', 'kind', 'title', 'message', 'item', 'item_title', 'item_status', 'claim', 'claim_status', 'claim_item', 'claim_item_title', 'conversation', 'match', 'moderation_report', 'is_read', 'created_at')
        read_only_fields = ('id', 'kind', 'title', 'message', 'item', 'item_title', 'item_status', 'claim', 'claim_status', 'claim_item', 'claim_item_title', 'conversation', 'match', 'moderation_report', 'created_at')

    def get_title(self, notification):
        return notification.title or notification.get_kind_display()


class MessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.name', read_only=True)

    class Meta:
        model = Message
        fields = ('id', 'sender', 'sender_name', 'message_text', 'sent_at', 'read_at')
        read_only_fields = ('id', 'sender', 'sender_name', 'sent_at', 'read_at')


class ConversationSerializer(serializers.ModelSerializer):
    item_title = serializers.CharField(source='item.title', read_only=True)
    other_participant_name = serializers.SerializerMethodField()
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = Conversation
        fields = (
            'id', 'item', 'item_title', 'claim', 'other_participant_name',
            'created_at', 'updated_at', 'last_message',
        )
        read_only_fields = ('id', 'created_at', 'updated_at', 'last_message')

    def get_other_participant_name(self, conversation):
        request = self.context.get('request')
        if request is None or not request.user.is_authenticated:
            return ''
        other = conversation.participants.exclude(pk=request.user.pk).order_by('pk').first()
        return other.name if other else ''

    def get_last_message(self, conversation):
        message = conversation.messages.last()
        return message.message_text if message else ''