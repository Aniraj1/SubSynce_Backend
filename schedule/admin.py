from django.contrib import admin

from schedule.model import cleaningschedule


admin.site.register(cleaningschedule.ServiceSchedule)
admin.site.register(cleaningschedule.ScheduleAssignment)
admin.site.register(cleaningschedule.ServiceOccurrence)
