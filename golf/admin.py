#-*- coding: utf-8 -*-

from django.contrib import admin
from models import *


class RegionAdmin(admin.ModelAdmin):
    list_display = ("name",)
admin.site.register(GolfRegion, RegionAdmin)


class GolfClubAdmin(admin.ModelAdmin):
    list_display = ("name",)
admin.site.register(GolfClub, GolfClubAdmin)


class PlayerAdmin(admin.ModelAdmin):
    list_display = ("pk", "first_name", "last_name", "email", "phone_number")
admin.site.register(Player, PlayerAdmin)


class UpdateAdmin(admin.ModelAdmin):
    list_display = ("filename", "filehash")
admin.site.register(Update, UpdateAdmin)


class UpdateLineAdmin(admin.ModelAdmin):
    list_display = ("pk", "player", "result", "handicap",
                    "region", "section", "division", "event_date", "golflink_number",
                    "home_golfclub", "host_golfclub", )
admin.site.register(UpdateLine, UpdateLineAdmin)


class LeaderBoardAdmin(admin.ModelAdmin):
    list_display = ("pk", "date", "region", "section", "division")
admin.site.register(LeaderBoard, LeaderBoardAdmin)


class LeaderBoardLineAdmin(admin.ModelAdmin):
    list_display = ("pk", "board", "player", "playoff_status", "latest_score", "curr_position", "prev_position", "movement", "curr_handicap", "top_round_1st", "top_round_2nd", "top_round_3rd")
admin.site.register(LeaderBoardLine, LeaderBoardLineAdmin)