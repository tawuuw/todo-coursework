from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST
from .forms import RegistrationForm, TaskForm
from .models import Section, Task


def register(request):
    if request.user.is_authenticated:
        return redirect("tasks:list")
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Аккаунт создан. Добро пожаловать!")
        return redirect("tasks:list")
    return render(request, "registration/register.html", {"form": form})


@login_required
def task_list(request):
    tasks = Task.objects.filter(owner=request.user).select_related("section")
    summary = tasks.aggregate(total=Count("id"), done=Count("id", filter=Q(completed=True)))
    summary["active"] = summary["total"] - summary["done"]
    selected_section = None
    section_id = request.GET.get("section", "")
    if section_id:
        if not section_id.isdecimal():
            section_id = "0"
        selected_section = get_object_or_404(Section, pk=int(section_id))
        tasks = tasks.filter(section=selected_section)
    status = request.GET.get("status", "all")
    if status not in ("all", "active", "done"):
        status = "all"
    if status != "all":
        tasks = tasks.filter(completed=status == "done")
    return render(request, "tasks/list.html", {
        "tasks": tasks, "sections": Section.objects.all(),
        "selected_section": selected_section, "status": status, "summary": summary,
    })


@login_required
def task_create(request):
    form = TaskForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        task = form.save(commit=False)
        task.owner = request.user
        task.save()
        messages.success(request, "Задача добавлена.")
        return redirect("tasks:list")
    return render(request, "tasks/form.html", {
        "form": form, "heading": "Новая задача", "button": "Добавить задачу",
        "has_sections": Section.objects.exists(),
    })


@login_required
def task_edit(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    form = TaskForm(request.POST or None, instance=task)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Изменения сохранены.")
        return redirect("tasks:list")
    return render(request, "tasks/form.html", {
        "form": form, "heading": "Редактирование задачи", "button": "Сохранить",
        "has_sections": True,
    })


@login_required
def task_delete(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    if request.method == "POST":
        task.delete()
        messages.success(request, "Задача удалена.")
        return redirect("tasks:list")
    return render(request, "tasks/delete.html", {"task": task})


@login_required
@require_POST
def task_toggle(request, pk):
    task = get_object_or_404(Task, pk=pk, owner=request.user)
    task.completed = not task.completed
    task.save(update_fields=["completed", "updated_at"])
    messages.success(request, "Задача выполнена." if task.completed else "Задача снова в работе.")
    return redirect("tasks:list")

