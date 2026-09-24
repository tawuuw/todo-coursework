from django.conf import settings
from django.db import models

class Section(models.Model):
    name = models.CharField("Название", max_length=80, unique=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "раздел"
        verbose_name_plural = "разделы"

    def __str__(self):
        return self.name


class Task(models.Model):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE,
        related_name="tasks", verbose_name="Пользователь"
    )
    section = models.ForeignKey(
        Section, on_delete=models.PROTECT, related_name="tasks",
        verbose_name="Раздел"
    )
    title = models.CharField("Название задачи", max_length=160)
    description = models.TextField("Описание", blank=True, max_length=3000)
    completed = models.BooleanField("Выполнена", default=False)
    created_at = models.DateTimeField("Создана", auto_now_add=True)
    updated_at = models.DateTimeField("Изменена", auto_now=True)

    class Meta:
        ordering = ["completed", "-created_at", "-pk"]
        verbose_name = "задача"
        verbose_name_plural = "задачи"

    def __str__(self):
        return self.title

