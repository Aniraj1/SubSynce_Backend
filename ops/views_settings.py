"""Company settings: business details, logo and default invoice terms (Owner only)."""
from django.contrib import messages
from django.shortcuts import redirect, render

from ops.access import OWNER, role_required
from ops.forms import CompanyProfileForm
from ops.models import CompanyProfile


@role_required(OWNER)
def company_settings_view(request):
    profile = CompanyProfile.load()
    old_logo = profile.logo.name
    form = CompanyProfileForm(request.POST or None, request.FILES or None, instance=profile)
    if request.method == "POST" and form.is_valid():
        profile = form.save()
        if old_logo and old_logo != profile.logo.name:
            profile.logo.storage.delete(old_logo)
        messages.success(request, "Company info saved.")
        return redirect("ops:company_settings")
    return render(request, "ops/settings/company.html", {"form": form, "profile": CompanyProfile.load()})
