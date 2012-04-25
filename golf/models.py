#-*- coding: utf-8 -*-

from django.db import models


class GolfRegion(models.Model):
    name = models.CharField(max_length=512, db_index=True)

    def __unicode__(self):
        return u"%s" % self.name


class GolfClub(models.Model):
    name = models.CharField(max_length=512, db_index=True)

    def __unicode__(self):
        return u"%s" % self.name


class Player(models.Model):

    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)

    # что мешает игрокам менять номера телефонов или емэйлы? или даже имена?
    email = models.EmailField(db_index=True, unique=True)
    phone_number = models.CharField(max_length=32)

    # что мешает игрока переходить в другие клубы или менять номер? причем прямо посреди сезона, или что там у них.
    golflink_number = models.CharField(max_length=32)
    home_golfclub = models.ForeignKey(GolfClub, related_name="homeclub_set")

    def __unicode__(self):
        return u"%s %s <%s>" % (self.first_name, self.last_name, self.email)


class Update(models.Model):

    filename = models.CharField(max_length=256)
    filehash = models.CharField(max_length=65, db_index=True, unique=True)

    def __unicode__(self):
        return u"%s (%s)" % (self.filename, self.filehash)


class UpdateLine(models.Model):

    update = models.ForeignKey(Update)

    player = models.ForeignKey(Player)

    region = models.ForeignKey(GolfRegion)
    section = models.CharField(max_length=8)
    division = models.CharField(max_length=16)

    event_date = models.DateField()

    host_golfclub = models.ForeignKey(GolfClub)

    result = models.IntegerField()
    handicap = models.IntegerField()



class LeaderBoard(models.Model):

    date = models.DateField()
    host_golfclub = models.ForeignKey(GolfClub)

    region = models.ForeignKey(GolfRegion, db_index=True)
    section = models.CharField(max_length=8, db_index=True, choices=(("A", "A"), ("B", "B")))
    division = models.CharField(max_length=16, db_index=True, choices=(("M1", "MEN 1"), ("M2", "MEN 2"), ("W1", "WOMEN 1"), ("W2", "WOMEN 2"), ("J", "JUNIOR")))

    scored_against = models.ForeignKey("LeaderBoard", null=True)

    def __unicode__(self):
        return u"%s <%s/%s/%s>" % (self.date, self.region, self.section, self.division)

    @staticmethod
    def date_choices():
        return [(r["date"], r["date"]) for r in LeaderBoard.objects.all().values("date").distinct()]



class LeaderBoardLine(models.Model):

    board = models.ForeignKey(LeaderBoard)
    player = models.ForeignKey(Player)

    playoff_status = models.CharField(max_length=4)
    latest_score = models.IntegerField()
    prev_position = models.IntegerField(null=True)
    curr_position = models.IntegerField(null=True)

    @property
    def movement(self):
        if self.playoff_status != "Q":
            return "NQ"
        if not self.curr_position or not self.prev_position:
            return "-"
        d = self.prev_position - self.curr_position
        if d > 0:
            d = "+%s" % d
        else:
            d = "%s" % d
        return d

    curr_handicap = models.IntegerField()

    top_round_1st = models.IntegerField()
    top_round_2nd = models.IntegerField()
    top_round_3rd = models.IntegerField()

    @property
    def top_round_avg(self):
        return ((self.top_round_1st or 0)+(self.top_round_2nd or 0)+(self.top_round_3rd or 0))/3.0


    class Meta:
        ordering = ("board", "-curr_position")