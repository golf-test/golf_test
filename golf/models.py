#-*- coding: utf-8 -*-

from django.db import models



class GolfClub(models.Model):
    name = models.CharField(max_length=512, db_index=True)

    def __unicode__(self):
        return u"%s" % self.name


class Player(models.Model):

    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)

    # что мешает игрокам менять номера телефонов или емэйлы? или даже имена? а шли бы они, редкое это событие, руками перебить можно будет.
    email = models.EmailField(db_index=True, unique=True)
    phone_number = models.CharField(max_length=32)

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

    region = models.CharField(max_length=64)
    section = models.CharField(max_length=8)
    division = models.CharField(max_length=16)

    event_date = models.DateField()

    # что мешает игрока переходить в другие клубы или менять номер? а ничего не мешает.
    golflink_number = models.CharField(max_length=32)
    home_golfclub = models.ForeignKey(GolfClub, related_name="homeclub_set")

    host_golfclub = models.ForeignKey(GolfClub, related_name="hostclub_set")

    result = models.IntegerField()
    handicap = models.IntegerField()



class LeaderBoard(models.Model):

    date = models.DateField()
    host_golfclub = models.ForeignKey(GolfClub)

    region = models.CharField(max_length=64)
    section = models.CharField(max_length=8)
    division = models.CharField(max_length=16)

    scored_against = models.ForeignKey("LeaderBoard", null=True)

    def __unicode__(self):
        return u"%s <%s/%s/%s>" % (self.date, self.region, self.section, self.division)



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
        return self.curr_position - self.prev_position

    curr_handicap = models.IntegerField()

    top_round_1st = models.IntegerField()
    top_round_2nd = models.IntegerField()
    top_round_3rd = models.IntegerField()

    @property
    def top_round_avg(self):
        return ((self.top_round_1st or 0)+(self.top_round_2nd or 0)+(self.top_round_3rd or 0))/3.0


    class Meta:
        ordering = ("board", "-curr_position")