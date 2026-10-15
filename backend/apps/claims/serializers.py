from rest_framework import serializers

from apps.items.models import Item
from .models import Claim, ClaimAnswer, VerificationQuestion


class VerificationQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = VerificationQuestion
        fields = ('id', 'item', 'question_text', 'is_active', 'created_at')
        read_only_fields = ('id', 'created_at')


class ClaimAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.question_text', read_only=True)

    class Meta:
        model = ClaimAnswer
        fields = ('id', 'question', 'question_text', 'answer_text', 'submitted_at')
        read_only_fields = ('id', 'question_text', 'submitted_at')


class ClaimSerializer(serializers.ModelSerializer):
    item = serializers.PrimaryKeyRelatedField(queryset=Item.objects.filter(item_type=Item.Type.FOUND))
    item_title = serializers.CharField(source='item.title', read_only=True)
    answers = ClaimAnswerSerializer(many=True, read_only=True)
    claimant_name = serializers.CharField(source='claimant.name', read_only=True)

    class Meta:
        model = Claim
        fields = ('id', 'item', 'item_title', 'claimant', 'claimant_name', 'status', 'evidence', 'answers', 'submitted_at', 'reviewed_at', 'decision_reason')
        read_only_fields = ('id', 'claimant', 'claimant_name', 'status', 'answers', 'submitted_at', 'reviewed_at', 'decision_reason')

    def validate_item(self, item):
        if item.reporter_id == self.context['request'].user.id:
            raise serializers.ValidationError('You cannot claim an item you reported finding.')
        if item.status != Item.Status.OPEN:
            raise serializers.ValidationError('This item is not accepting claims.')
        if Claim.objects.filter(item=item, claimant=self.context['request'].user).exists():
            raise serializers.ValidationError('You already submitted a claim for this item.')
        return item

    def create(self, validated_data):
        return Claim.objects.create(claimant=self.context['request'].user, **validated_data)