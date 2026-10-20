from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('communication', '0003_notification_targets'),
    ]

    operations = [
        migrations.AlterField(
            model_name='conversation',
            name='claim',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.PROTECT, related_name='conversations', to='claims.claim'),
        ),
    ]