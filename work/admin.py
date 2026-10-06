from django.contrib import admin

from work.model import workcomplete


admin.site.register(workcomplete.CompleteWork)
admin.site.register(workcomplete.WorkCompleteImage)