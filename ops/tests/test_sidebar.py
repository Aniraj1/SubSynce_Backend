from django.test import TestCase
from django.urls import reverse

from ops.tests.helpers import login, make_user


class SidebarTests(TestCase):
    def _sidebar(self, resp):
        html = resp.content.decode()
        return html[html.index("<aside"):html.index("</aside>")]

    def test_staff_sidebar_has_company_info_but_no_users_or_logout(self):
        for role in ("OWNER", "ADMINISTRATOR"):
            self.client.logout()
            login(self.client, make_user(role))
            resp = self.client.get(reverse("ops:dashboard"))
            sidebar = self._sidebar(resp)
            self.assertIn("Company Info", sidebar)
            self.assertNotIn(reverse("ops:users"), sidebar)
            self.assertNotIn(reverse("ops:logout"), sidebar)
            # Still reachable from the top-right account menu.
            self.assertContains(resp, reverse("ops:users"))
            self.assertContains(resp, reverse("ops:logout"))

    def test_contractor_sidebar_has_no_logout_but_menu_does(self):
        login(self.client, make_user("CONTRACTOR"))
        resp = self.client.get(reverse("ops:invoices"))
        self.assertNotIn(reverse("ops:logout"), self._sidebar(resp))
        self.assertContains(resp, reverse("ops:logout"))

    def test_company_page_is_titled_company_info(self):
        login(self.client, make_user("OWNER"))
        resp = self.client.get(reverse("ops:company_settings"))
        self.assertContains(resp, ">Company Info</h1>")
