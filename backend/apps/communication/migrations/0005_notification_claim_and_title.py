from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('claims', '0001_initial'),
        ('communication', '0004_allow_item_conversations'),
    ]

    operations = [
        migrations.AddField(
            model_name='notification',
            name='title',
            field=models.CharField(blank=True, default='', max_length=140),
        ),
        migrations.AddField(
            model_name='notification',
            name='claim',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='notifications', to='claims.claim'),
        ),
    ]