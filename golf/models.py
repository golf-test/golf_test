#-*- coding: utf-8 -*-

from django.db import models



class GolfClub(models.Model):
    name = models.CharField(max_length=512)



class Player(models.Model):

    first_name = models.CharField(max_length=256)
    last_name = models.CharField(max_length=256)

    email = models.EmailField()
    phone_number = models.CharField(max_length=32)

    home_golfclub = models.ForeignKey(GolfClub)
    golflink_number = models.CharField(max_length=32)




class Update(models.Model):

    filename = models.CharField(max_length=256)



class UpdateLine(models.Model):

    update = models.ForeignKey(Update)

    player = models.ForeignKey(Player)

    region = models.CharField(max_length=64)
    section = models.CharField(max_length=8)
    division = models.CharField(max_length=16)

    event_date = models.DateField()
    host_golfclub = models.ForeignKey(GolfClub)

    result = models.IntegerField()
    handicap = models.IntegerField()



class LeaderBoard(models.Model):

    date = models.DateField()



class LeaderBoardLine(models.Model):

    board = models.ForeignKey(LeaderBoard)
    player = models.ForeignKey(Player)

    prev_update_line = models.ForeignKey(UpdateLine, null=True)
    curr_update_line = models.ForeignKey(UpdateLine)

    playoff_status = models.CharField(max_length=4)
    latest_score = models.IntegerField()
    prev_position = models.IntegerField()
    curr_position = models.IntegerField()

    @property
    def movement(self):
        return self.curr_position - self.prev_position

    curr_handicap = models.IntegerField()

    top_round_1st = models.IntegerField()
    top_round_2nd = models.IntegerField()
    top_round_3rd = models.IntegerField()



