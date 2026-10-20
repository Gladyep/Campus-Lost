from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0002_extend_conversation'),
        ('matching', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='conversation',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='communication.conversation'),
        ),
        migrations.AddField(
            model_name='notification',
            name='match',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='matching.match'),
        ),
        migrations.AlterField(
            model_name='notification',
            name='kind',
            field=models.CharField(choices=[('REPORT', 'New community report'), ('MATCH', 'Potential match'), ('CLAIM', 'Claim update'), ('MESSAGE', 'New message'), ('STATUS', 'Item status'), ('MODERATION', 'Moderation update')], max_length=16),
        ),
    ]