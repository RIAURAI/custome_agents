from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='userintegration',
            name='service',
            field=models.CharField(
                choices=[
                    ('microsoft', 'Microsoft (Outlook + Teams)'),
                    ('google', 'Google Workspace (Gmail + Calendar + Meet)'),
                    ('slack', 'Slack'),
                    ('calendly', 'Calendly'),
                ],
                max_length=50,
            ),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='slack_team_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='slack_team_name',
            field=models.CharField(blank=True, max_length=255),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='slack_user_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='slack_bot_user_id',
            field=models.CharField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='slack_app_token_enc',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='slack_signing_secret_enc',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='slack_user_token_enc',
            field=models.BinaryField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='calendly_organization_uri',
            field=models.CharField(blank=True, max_length=500),
        ),
        migrations.AddField(
            model_name='userintegration',
            name='calendly_user_uri',
            field=models.CharField(blank=True, max_length=500),
        ),
    ]
