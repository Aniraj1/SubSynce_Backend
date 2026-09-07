from django.contrib import admin

from client.model import clientmanage


admin.site.register(clientmanage.Client)
admin.site.register(clientmanage.Site)
admin.site.register(clientmanage.SiteImage)
