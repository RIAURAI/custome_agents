from django.contrib.auth.models import User
from django.test import TestCase, RequestFactory
from django.urls import reverse

from companies.models import Company, Membership
from integrations.models import CompanyIntegration


class CompanyIntegrationModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user("admin", password="pw")
        self.company = Company.objects.create(name="Acme")
        Membership.objects.create(user=self.user, company=self.company, role=Membership.Role.OWNER)

    def test_create_integration(self):
        ci = CompanyIntegration.objects.create(
            company=self.company,
            service="microsoft",
            connected_by=self.user,
        )
        self.assertEqual(ci.status, "active")
        self.assertEqual(str(ci), "Acme → microsoft (active)")

    def test_unique_company_service(self):
        CompanyIntegration.objects.create(company=self.company, service="microsoft")
        with self.assertRaises(Exception):
            CompanyIntegration.objects.create(company=self.company, service="microsoft")

    def test_multiple_services_per_company(self):
        CompanyIntegration.objects.create(company=self.company, service="microsoft")
        CompanyIntegration.objects.create(company=self.company, service="slack")
        self.assertEqual(self.company.integrations.count(), 2)


class IntegrationAccessControlTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_user("admin", password="VeryStrongPass123!")
        self.member_user = User.objects.create_user("member", password="VeryStrongPass123!")
        self.company = Company.objects.create(name="Acme")
        Membership.objects.create(user=self.admin_user, company=self.company, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.member_user, company=self.company, role=Membership.Role.MEMBER)

    def test_admin_can_access_connect_page(self):
        self.client.login(username="admin", password="VeryStrongPass123!")
        response = self.client.get(reverse("integrations:connect"))
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["is_admin"])

    def test_member_sees_connect_page_but_not_admin(self):
        self.client.login(username="member", password="VeryStrongPass123!")
        response = self.client.get(reverse("integrations:connect"))
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["is_admin"])

    def test_member_cannot_trigger_microsoft_connect(self):
        self.client.login(username="member", password="VeryStrongPass123!")
        response = self.client.get(reverse("integrations:microsoft_connect"))
        # Should redirect back to connect page (admin check)
        self.assertEqual(response.status_code, 302)

    def test_member_cannot_trigger_slack_connect(self):
        self.client.login(username="member", password="VeryStrongPass123!")
        response = self.client.get(reverse("integrations:slack_connect"))
        self.assertEqual(response.status_code, 302)

    def test_connect_view_shows_company_integrations(self):
        CompanyIntegration.objects.create(
            company=self.company, service="microsoft", connected_by=self.admin_user
        )
        self.client.login(username="member", password="VeryStrongPass123!")
        response = self.client.get(reverse("integrations:connect"))
        self.assertIn("microsoft", response.context["integrations"])

