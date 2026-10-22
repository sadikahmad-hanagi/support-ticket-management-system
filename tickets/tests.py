from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from .models import Ticket

User = get_user_model()


class CustomerTicketTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer1",
            password="test-password-123",
        )
        self.other_customer = User.objects.create_user(
            username="customer2",
            password="test-password-123",
        )

    def create_ticket(self, user, title="Test ticket"):
        return Ticket.objects.create(
            title=title,
            description="A test description",
            category=Ticket.Category.BUG,
            created_by=user,
        )

    def test_anonymous_users_are_redirected(self):
        ticket = self.create_ticket(self.customer)

        urls = [
            reverse("tickets"),
            reverse("ticket_create"),
            reverse("ticket_detail", kwargs={"ticket_id": ticket.pk}),
        ]

        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn("/accounts/login/", response.url)

    def test_customer_can_create_ticket(self):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("ticket_create"),
            {
                "title": "Login issue",
                "description": "I cannot log in",
                "category": "BUG",
                "priority": "HIGH",
            },
        )

        ticket = Ticket.objects.get(title="Login issue")

        self.assertRedirects(
            response,
            reverse("ticket_detail", kwargs={"ticket_id": ticket.pk}),
        )
        self.assertEqual(ticket.created_by, self.customer)
        self.assertEqual(ticket.priority, "HIGH")
        self.assertEqual(ticket.status, Ticket.Status.OPEN)
        self.assertIsNone(ticket.assigned_to)

    def test_customer_cannot_set_protected_fields(self):
        self.client.force_login(self.customer)

        self.client.post(
            reverse("ticket_create"),
            {
                "title": "Forged ticket",
                "description": "Testing protected fields",
                "category": "BUG",
                "priority": "MEDIUM",
                "created_by": self.other_customer.pk,
                "assigned_to": self.other_customer.pk,
                "status": "CLOSED",
            },
        )

        ticket = Ticket.objects.get(title="Forged ticket")

        self.assertEqual(ticket.created_by, self.customer)
        self.assertIsNone(ticket.assigned_to)
        self.assertEqual(ticket.status, Ticket.Status.OPEN)

    def test_invalid_submission_does_not_create_ticket(self):
        self.client.force_login(self.customer)

        response = self.client.post(
            reverse("ticket_create"),
            {
                "title": "",
                "description": "Missing title",
                "category": "BUG",
                "priority": "MEDIUM",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(Ticket.objects.count(), 0)

    def test_list_contains_only_own_tickets(self):
        own_ticket = self.create_ticket(self.customer, "My ticket")
        self.create_ticket(self.other_customer, "Someone else's ticket")

        self.client.force_login(self.customer)
        response = self.client.get(reverse("tickets"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, own_ticket.title)
        self.assertNotContains(response, "Someone else's ticket")

    def test_customer_cannot_view_another_customers_ticket(self):
        ticket = self.create_ticket(self.other_customer)
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("ticket_detail", kwargs={"ticket_id": ticket.pk})
        )

        self.assertEqual(response.status_code, 404)

    def test_customer_can_view_own_ticket(self):
        ticket = self.create_ticket(self.customer)
        self.client.force_login(self.customer)

        response = self.client.get(
            reverse("ticket_detail", kwargs={"ticket_id": ticket.pk})
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, ticket.title)
        self.assertContains(response, ticket.description)

    def test_empty_ticket_list(self):
        self.client.force_login(self.customer)

        response = self.client.get(reverse("tickets"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "You haven't created any tickets yet.")


class AgentQueueTests(TestCase):
    def setUp(self):
        self.customer = User.objects.create_user(
            username="customer",
            password="test-password-123",
            role="CUSTOMER",
        )
        self.other_customer = User.objects.create_user(
            username="other_customer",
            password="test-password-123",
            role="CUSTOMER",
        )
        self.agent = User.objects.create_user(
            username="agent",
            password="test-password-123",
            role="AGENT",
        )
        self.other_agent = User.objects.create_user(
            username="other_agent",
            password="test-password-123",
            role="AGENT",
        )

        self.ticket = Ticket.objects.create(
            title="Login issue",
            description="Cannot log in",
            category=Ticket.Category.BUG,
            created_by=self.customer,
        )

    def test_anonymous_user_is_redirected_from_agent_queue(self):
        response = self.client.get(reverse("agent_queue"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("/accounts/login/", response.url)

    def test_customer_gets_forbidden_from_agent_queue(self):
        self.client.force_login(self.customer)
        response = self.client.get(reverse("agent_queue"))
        self.assertEqual(response.status_code, 403)

    def test_agent_sees_tickets_from_different_customers(self):
        Ticket.objects.create(
            title="Billing issue",
            description="Question about billing",
            category=Ticket.Category.BILLING,
            created_by=self.other_customer,
        )

        self.client.force_login(self.agent)
        response = self.client.get(reverse("agent_queue"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login issue")
        self.assertContains(response, "Billing issue")

    def test_status_filter_shows_only_matching_tickets(self):
        Ticket.objects.create(
            title="Resolved issue",
            description="Already fixed",
            category=Ticket.Category.GENERAL,
            status=Ticket.Status.RESOLVED,
            created_by=self.customer,
        )

        self.client.force_login(self.agent)
        response = self.client.get(
            reverse("agent_queue"),
            {"status": Ticket.Status.OPEN},
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Login issue")
        self.assertNotContains(response, "Resolved issue")

    def test_invalid_status_does_not_crash(self):
        self.client.force_login(self.agent)
        response = self.client.get(
            reverse("agent_queue"),
            {"status": "NOT_A_STATUS"},
        )
        self.assertEqual(response.status_code, 200)

    def test_agent_can_assign_ticket_to_another_agent(self):
        self.client.force_login(self.agent)
        response = self.client.post(
            reverse("ticket_assign", kwargs={"ticket_id": self.ticket.pk}),
            {"assignee": self.other_agent.pk},
        )

        self.assertRedirects(response, reverse("agent_queue"))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.other_agent)

    def test_agent_can_unassign_ticket(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()

        self.client.force_login(self.agent)
        self.client.post(
            reverse("ticket_assign", kwargs={"ticket_id": self.ticket.pk}),
            {"assignee": ""},
        )

        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_to)

    def test_customer_cannot_assign_ticket(self):
        self.client.force_login(self.customer)
        response = self.client.post(
            reverse("ticket_assign", kwargs={"ticket_id": self.ticket.pk}),
            {"assignee": self.agent.pk},
        )
        self.assertEqual(response.status_code, 403)

    def test_customer_cannot_be_assigned_as_agent(self):
        self.client.force_login(self.agent)
        response = self.client.post(
            reverse("ticket_assign", kwargs={"ticket_id": self.ticket.pk}),
            {"assignee": self.other_customer.pk},
        )

        self.ticket.refresh_from_db()
        self.assertIsNone(self.ticket.assigned_to)

    def test_get_does_not_change_assignment(self):
        self.ticket.assigned_to = self.agent
        self.ticket.save()

        self.client.force_login(self.agent)
        response = self.client.get(
            reverse("ticket_assign", kwargs={"ticket_id": self.ticket.pk}),
        )

        self.assertRedirects(response, reverse("agent_queue"))
        self.ticket.refresh_from_db()
        self.assertEqual(self.ticket.assigned_to, self.agent)
