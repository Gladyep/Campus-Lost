from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0005_notification_claim_and_title'),
        ('moderation', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='moderation_report',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='moderation.report'),
        ),
    ]