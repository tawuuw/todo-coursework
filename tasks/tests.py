from django.contrib.auth.models import User
from django.db.models.deletion import ProtectedError
from django.test import Client, TestCase
from django.urls import reverse
from .models import Section, Task


class TodoTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = User.objects.create_user("student", password="Check-pass-825!")
        cls.other = User.objects.create_user("other", password="Check-pass-825!")
        cls.admin = User.objects.create_superuser("admin", password="Admin-pass-925!")
        cls.section = Section.objects.create(name="Учёба")
        cls.second_section = Section.objects.create(name="Личное")
        cls.task = Task.objects.create(title="Подготовить отчёт", owner=cls.user, section=cls.section)
        cls.foreign_task = Task.objects.create(title="Чужая задача", owner=cls.other, section=cls.section)

    def setUp(self):
        self.client.force_login(self.user)

    def test_registration_creates_user_with_hashed_password(self):
        self.client.logout()
        response = self.client.post(reverse("register"), {
            "username": "new_student", "password1": "Safe-todo-672!",
            "password2": "Safe-todo-672!",
        })
        self.assertRedirects(response, reverse("tasks:list"))
        user = User.objects.get(username="new_student")
        self.assertTrue(user.check_password("Safe-todo-672!"))
        self.assertNotEqual(user.password, "Safe-todo-672!")
        self.assertFalse(user.is_staff)

    def test_duplicate_registration_rejected(self):
        self.client.logout()
        response = self.client.post(reverse("register"), {
            "username": "student", "password1": "Safe-todo-672!",
            "password2": "Safe-todo-672!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(User.objects.filter(username="student").count(), 1)

    def test_login_valid_and_invalid_password(self):
        self.client.logout()
        self.assertFalse(self.client.login(username="student", password="wrong"))
        self.assertTrue(self.client.login(username="student", password="Check-pass-825!"))

    def test_anonymous_user_redirected(self):
        self.client.logout()
        for url in (reverse("tasks:list"), reverse("tasks:create"),
                    reverse("tasks:edit", args=[self.task.pk]),
                    reverse("tasks:delete", args=[self.task.pk])):
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)

    def test_user_sees_only_own_tasks(self):
        response = self.client.get(reverse("tasks:list"))
        self.assertContains(response, self.task.title)
        self.assertNotContains(response, self.foreign_task.title)
        self.assertEqual(response.context["summary"]["total"], 1)

    def test_create_task_assigns_authenticated_owner(self):
        response = self.client.post(reverse("tasks:create"), {
            "title": "Прочитать методичку", "section": self.section.pk,
            "description": "Раздел 1", "owner": self.other.pk, "completed": True,
        })
        self.assertRedirects(response, reverse("tasks:list"))
        task = Task.objects.get(title="Прочитать методичку")
        self.assertEqual(task.owner, self.user)
        self.assertFalse(task.completed)

    def test_invalid_task_not_saved(self):
        count = Task.objects.count()
        for title, section in (("", self.section.pk), (" " * 3, self.section.pk),
                               ("А" * 161, self.section.pk), ("Тест", 9999)):
            with self.subTest(title=title, section=section):
                response = self.client.post(reverse("tasks:create"), {
                    "title": title, "section": section,
                })
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["form"].errors)
        self.assertEqual(Task.objects.count(), count)

    def test_edit_own_task(self):
        response = self.client.post(reverse("tasks:edit", args=[self.task.pk]), {
            "title": "Новая формулировка", "section": self.second_section.pk,
            "description": "Уточнение",
        })
        self.assertEqual(response.status_code, 302)
        self.task.refresh_from_db()
        self.assertEqual(self.task.title, "Новая формулировка")
        self.assertEqual(self.task.section, self.second_section)

    def test_foreign_task_protected_for_all_actions(self):
        for action in ("edit", "delete", "toggle"):
            with self.subTest(action=action):
                url = reverse("tasks:" + action, args=[self.foreign_task.pk])
                response = self.client.post(url, {
                    "title": "Попытка изменения", "section": self.section.pk,
                })
                self.assertEqual(response.status_code, 404)
        self.foreign_task.refresh_from_db()
        self.assertEqual(self.foreign_task.title, "Чужая задача")
        self.assertFalse(self.foreign_task.completed)

    def test_toggle_requires_post_and_can_be_reversed(self):
        url = reverse("tasks:toggle", args=[self.task.pk])
        self.assertEqual(self.client.get(url).status_code, 405)
        for expected in (True, False):
            self.assertEqual(self.client.post(url).status_code, 302)
            self.task.refresh_from_db()
            self.assertEqual(self.task.completed, expected)

    def test_delete_confirmation_and_post(self):
        url = reverse("tasks:delete", args=[self.task.pk])
        self.assertEqual(self.client.get(url).status_code, 200)
        self.assertTrue(Task.objects.filter(pk=self.task.pk).exists())
        self.assertEqual(self.client.post(url).status_code, 302)
        self.assertFalse(Task.objects.filter(pk=self.task.pk).exists())

    def test_section_and_status_filters(self):
        Task.objects.create(title="Готовая задача", section=self.second_section,
                            owner=self.user, completed=True)
        response = self.client.get(reverse("tasks:list"), {
            "section": self.second_section.pk, "status": "done"
        })
        self.assertContains(response, "Готовая задача")
        self.assertNotContains(response, self.task.title)
        self.assertEqual(response.context["summary"]["done"], 1)

    def test_invalid_section_returns_404(self):
        for value in ("missing", "-1", "9999"):
            self.assertEqual(self.client.get(reverse("tasks:list"), {"section": value}).status_code, 404)

    def test_csrf_blocks_untrusted_change(self):
        client = Client(enforce_csrf_checks=True)
        client.force_login(self.user)
        self.assertEqual(client.post(reverse("tasks:toggle", args=[self.task.pk])).status_code, 403)

    def test_html_in_title_is_escaped(self):
        self.task.title = '<script>alert("test")</script>'
        self.task.save()
        response = self.client.get(reverse("tasks:list"))
        self.assertContains(response, "&lt;script&gt;")
        self.assertNotContains(response, '<script>alert("test")</script>')

    def test_admin_pages_require_staff(self):
        urls = (reverse("admin:index"), reverse("admin:tasks_section_changelist"),
                reverse("admin:tasks_task_change", args=[self.task.pk]))
        for url in urls:
            with self.subTest(url=url):
                self.assertEqual(self.client.get(url).status_code, 302)
        self.client.force_login(self.admin)
        for url in urls:
            self.assertEqual(self.client.get(url).status_code, 200)

    def test_admin_manages_sections_and_tasks(self):
        self.client.force_login(self.admin)
        response = self.client.post(reverse("admin:tasks_section_add"), {"name": "Работа", "_save": "1"})
        self.assertEqual(response.status_code, 302)
        section = Section.objects.get(name="Работа")
        response = self.client.post(reverse("admin:tasks_section_change", args=[section.pk]),
                                    {"name": "Проекты", "_save": "1"})
        self.assertEqual(response.status_code, 302)
        section.refresh_from_db()
        self.assertEqual(section.name, "Проекты")
        response = self.client.post(reverse("admin:tasks_task_change", args=[self.foreign_task.pk]), {
            "owner": self.other.pk, "section": self.section.pk,
            "title": "Исправлено администратором", "description": "", "completed": "on", "_save": "1",
        })
        self.assertEqual(response.status_code, 302)
        self.foreign_task.refresh_from_db()
        self.assertTrue(self.foreign_task.completed)
        self.assertEqual(self.foreign_task.title, "Исправлено администратором")
        response = self.client.post(reverse("admin:tasks_task_delete", args=[self.foreign_task.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Task.objects.filter(pk=self.foreign_task.pk).exists())
        response = self.client.post(reverse("admin:tasks_section_delete", args=[section.pk]), {"post": "yes"})
        self.assertEqual(response.status_code, 302)
        self.assertFalse(Section.objects.filter(pk=section.pk).exists())

    def test_section_with_tasks_is_protected(self):
        with self.assertRaises(ProtectedError):
            self.section.delete()

    def test_logout_requires_post(self):
        self.assertEqual(self.client.get(reverse("logout")).status_code, 405)
        self.assertEqual(self.client.post(reverse("logout")).status_code, 302)
        self.assertNotIn("_auth_user_id", self.client.session)

    def test_empty_database_has_clear_message(self):
        Task.objects.all().delete()
        Section.objects.all().delete()
        response = self.client.get(reverse("tasks:create"))
        self.assertContains(response, "Сначала администратор должен создать")

