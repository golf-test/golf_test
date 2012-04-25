#-*- coding: utf-8 -*-

from django.shortcuts import render_to_response
from django.template.context import RequestContext
from django import forms

from models import *



def render_to(template_path):
    def decorator(func):
        def wrapper(request, *args, **kw):
            output = func(request, *args, **kw)
            if not isinstance(output, dict):
                return output
            return render_to_response(template_path, output,
                context_instance=RequestContext(request))
        return wrapper
    return decorator




class LeaderboardForm(forms.ModelForm):

    class Meta:
        model = LeaderBoard

    def __init__(self, *args, **kwargs):
        super(LeaderboardForm, self).__init__(*args, **kwargs)
        self.fields['date'].widget = forms.Select(choices=[("", "---------"),]+LeaderBoard.date_choices())


@render_to("leaderboard.html")
def leaderboard(request):

    form = LeaderboardForm(request.GET)

    q = models.Q()
    if "date" in form.data and form.data["date"]:
        q &= models.Q(date=form.data["date"])

    if "region" in form.data and form.data["region"]:
        q &= models.Q(region__pk=form.data["region"])

    if "host_golfclub" in form.data and form.data["host_golfclub"]:
        q &= models.Q(host_golfclub__pk=form.data["host_golfclub"])

    if "division" in form.data and form.data["division"]:
        q &= models.Q(division=form.data["division"])

    if "section" in form.data and form.data["section"]:
        q &= models.Q(section=form.data["section"])

    if LeaderBoard.objects.filter(q).count():
        board = LeaderBoard.objects.filter(q).order_by("-date")[0]
        lines = board.leaderboardline_set.select_related().all().order_by("-playoff_status", "curr_position")

        fields = {}
        fields["date"] = board.date
        fields["division"] = board.division
        fields["section"] = board.section
        fields["host_golfclub"] = board.host_golfclub_id
        fields["region"] = board.region_id

        form = LeaderboardForm(fields)

    else:
        board = None
        lines = []

    return vars()