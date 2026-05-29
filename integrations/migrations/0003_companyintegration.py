import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('companies', '0001_initial'),
        ('integrations', '0002_userintegration_slack_calendly_fields'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CompanyIntegration',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('service', models.CharField(
                    choices=[
                        ('microsoft', 'Microsoft (Outlook + Teams)'),
                        ('google', 'Google Workspace (Gmail + Calendar + Meet)'),
                        ('slack', 'Slack'),
                        ('calendly', 'Calendly'),
                        ('discord', 'Discord'),
                        ('jira', 'Jira'),
                    ],
                    max_length=50,
                )),
                ('status', models.CharField(
                    choices=[
                        ('active', 'Active'),
                        ('expired', 'Token Expired'),
                        ('error', 'Error'),
                        ('disconnected', 'Disconnected'),
                    ],
                    default='active',
                    max_length=20,
                )),
                ('access_token_enc', models.BinaryField(blank=True, null=True)),
                ('refresh_token_enc', models.BinaryField(blank=True, null=True)),
                ('token_expiry', models.DateTimeField(blank=True, null=True)),
                ('ms_client_id_enc', models.BinaryField(blank=True, null=True)),
                ('ms_client_secret_enc', models.BinaryField(blank=True, null=True)),
                ('ms_tenant_id', models.CharField(blank=True, default='common', max_length=100)),
                ('ms_account_name', models.CharField(blank=True, max_length=255)),
                ('ms_account_email', models.CharField(blank=True, max_length=255)),
                ('enabled_ms_features', models.JSONField(blank=True, default=list)),
                ('slack_team_id', models.CharField(blank=True, max_length=100)),
                ('slack_team_name', models.CharField(blank=True, max_length=255)),
                ('slack_user_id', models.CharField(blank=True, max_length=100)),
                ('slack_bot_user_id', models.CharField(blank=True, max_length=100)),
                ('slack_app_token_enc', models.BinaryField(blank=True, null=True)),
                ('slack_signing_secret_enc', models.BinaryField(blank=True, null=True)),
                ('slack_user_token_enc', models.BinaryField(blank=True, null=True)),
                ('google_account_name', models.CharField(blank=True, max_length=255)),
                ('google_account_email', models.CharField(blank=True, max_length=255)),
                ('google_project_id', models.CharField(blank=True, max_length=255)),
                ('google_client_id_enc', models.BinaryField(blank=True, null=True)),
                ('google_client_secret_enc', models.BinaryField(blank=True, null=True)),
                ('calendly_organization_uri', models.CharField(blank=True, max_length=500)),
                ('calendly_user_uri', models.CharField(blank=True, max_length=500)),
                ('calendly_client_id_enc', models.BinaryField(blank=True, null=True)),
                ('calendly_client_secret_enc', models.BinaryField(blank=True, null=True)),
                ('discord_guild_id', models.CharField(blank=True, max_length=100)),
                ('discord_guild_name', models.CharField(blank=True, max_length=255)),
                ('discord_bot_token_enc', models.BinaryField(blank=True, null=True)),
                ('discord_webhook_url', models.URLField(blank=True, max_length=500)),
                ('jira_site_url', models.URLField(blank=True, help_text='e.g. https://yourteam.atlassian.net', max_length=500)),
                ('jira_project_key', models.CharField(blank=True, max_length=50)),
                ('jira_user_email', models.CharField(blank=True, max_length=255)),
                ('jira_api_token_enc', models.BinaryField(blank=True, null=True)),
                ('connected_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('company', models.ForeignKey(
                    on_delete=django.db.models.deletion.CASCADE,
                    related_name='integrations',
                    to='companies.company',
                )),
                ('connected_by', models.ForeignKey(
                    blank=True,
                    null=True,
                    on_delete=django.db.models.deletion.SET_NULL,
                    related_name='connected_integrations',
                    to=settings.AUTH_USER_MODEL,
                )),
            ],
            options={
                'unique_together': {('company', 'service')},
            },
        ),
    ]
