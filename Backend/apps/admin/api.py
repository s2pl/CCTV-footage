from ninja import NinjaAPI, Schema
from typing import List
from .models import AdminPanel
from django.shortcuts import get_object_or_404
from django.middleware.csrf import get_token
from django.http import JsonResponse

api = NinjaAPI(urls_namespace='admin_system')

class AdminPanelSchema(Schema):
    id: int
    name: str
    description: str
    status: str
    some_critical_field: str

class AdminPanelCreateSchema(Schema):
    name: str
    description: str
    status: str
    some_critical_field: str

@api.get("/panels", response=List[AdminPanelSchema])
def list_panels(request):
    return AdminPanel.objects.all()

@api.get("/panels/{panel_id}", response=AdminPanelSchema)
def get_panel(request, panel_id: int):
    return get_object_or_404(AdminPanel, id=panel_id)

@api.post("/panels", response=AdminPanelSchema)
def create_panel(request, payload: AdminPanelCreateSchema):
    panel = AdminPanel.objects.create(**payload.dict())
    return panel

@api.delete("/panels/{panel_id}")
def delete_panel(request, panel_id: int):
    panel = get_object_or_404(AdminPanel, id=panel_id)
    panel.delete()
    return {"success": True}

@api.get("/csrf-token")
def get_csrf_token(request):
    """Get CSRF token for the current session"""
    return JsonResponse({
        "csrfToken": get_token(request)
    }) 