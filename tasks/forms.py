from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Task

class RegistrationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ("username",)


class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ("title", "section", "description")
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "Например, подготовить отчёт"}),
            "description": forms.Textarea(attrs={
                "rows": 4, "placeholder": "Детали задачи (необязательно)"
            }),
        }

