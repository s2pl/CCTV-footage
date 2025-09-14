from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import AdminPanel

@staff_member_required
def admin_view_details(request, id):
    obj = get_object_or_404(AdminPanel, id=id)
    context = {
        'object': obj,
        'title': f'Details for {obj.name}',
    }
    return render(request, 'admin/view_details.html', context)

@staff_member_required
def admin_process_item(request, id):
    obj = get_object_or_404(AdminPanel, id=id)
    try:
        # Add your processing logic here
        messages.success(request, f'Successfully processed {obj.name}')
    except Exception as e:
        messages.error(request, f'Error processing {obj.name}: {str(e)}')
    
    return HttpResponseRedirect(request.META.get('HTTP_REFERER', '/')) 