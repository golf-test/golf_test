#-*- coding: utf-8 -*-
import os, sys

sys.path.append("..")
sys.path.append("../..")
os.environ["DJANGO_SETTINGS_MODULE"] = "golf_test.settings"

import csv
from itertools import chain
from hashlib import sha256
from time import strptime
from datetime import date
import re
from pprint import pprint


from django.db import transaction, models

from golf.models import *


def parse_date(s):
    if re.search("\d{4}\.\d+.\d+", s):
        t = strptime(s, "%Y.%m.%d")
    elif re.search("\d{2}\.\d+.\d+", s):
        t = strptime(s, "%y.%m.%d")
    elif re.search("\d+/\d+/\d+", s):
        t = strptime(s, "%m/%d/%Y")
    else:
        raise RuntimeError("Date parsing error: %s" % s)
    return date(year=t.tm_year, month=t.tm_mon, day=t.tm_mday)



@transaction.commit_on_success
def load_csv(csv_file_name, overwrite=True):
    h = sha256()
    with file(csv_file_name, 'rb') as csv_fl:
        while True:
            dat = csv_fl.read(65535)
            if not dat:
                break
            h.update(dat)
    csv_file_hash = h.hexdigest()
    if Update.objects.filter(filehash=csv_file_hash).count():
        if not overwrite:
            print "file already parsed!!!"
            return False
        else:
            Update.objects.filter(filehash=csv_file_hash).delete()
    update_obj = Update.objects.create(filename=csv_file_name, filehash=csv_file_hash)
    with file(csv_file_name, 'rb') as csv_fl:
        rdr = csv.DictReader(csv_fl, delimiter=';')
        csv_records = [rec for rec in rdr]

    # заполнить клубы
    clubs = set(
        chain(
            (rec["Home Golf Club"] for rec in csv_records),
            (rec["Host Golf Club"] for rec in csv_records),
        )
    )
    # вытащить из базы найденые имена клубов
    clubs_in_db = set((c["name"] for c in GolfClub.objects.filter(name__in=clubs).values("name")))
    # новые клубы добавить в базу
    clubs_new = clubs - clubs_in_db
    for club_name in clubs_new:
        club_obj = GolfClub.objects.create(name=club_name)

    # собственно клубы
    clubs_map = dict(((club_obj.name, club_obj) for club_obj in GolfClub.objects.all()))

    # теперь залить всех игроков
    # что считать ключом игрока?
    # емэйл? на этом и порешим. хватит для тестового задания.
    for rec in csv_records:
        # если игрока нет - создаем
        try:
            player_obj = Player.objects.get(email=rec["Email"])
        except Player.DoesNotExist:
            player_obj = Player.objects.create(
                first_name=rec["Firstname"],
                last_name=rec["Surname"],
                email=rec["Email"],
                phone_number=rec["Phone"],
            )

        # пишем данные в UpdateLine
        update_line_obj = update_obj.updateline_set.create(
            player=player_obj,
            region=rec["Golf Region"],
            section=rec["Section"],
            division=rec["Division"],
            event_date=parse_date(rec["Event Date"]),
            golflink_number=rec["Golf Link Number"],
            home_golfclub=clubs_map[rec["Home Golf Club"]],
            host_golfclub=clubs_map[rec["Host Golf Club"]],
            result=rec["Result"],
            handicap=rec["Handicap"],
        )

    return True


@transaction.commit_on_success
def fill_leaderboards():
    # раздробить все данные на регион\секцию\дивизион (хост-клуб региона сюда-же)
    for host_club_id, region, section, division in UpdateLine.objects.all().values_list("host_golfclub", "region", "section", "division").distinct():
        # теперь можно посчитать лидерборды за те даты, за которые они не посчитаны.
        for (upd_date,) in UpdateLine.objects.all().values_list("event_date").distinct().order_by("event_date"):
            date_lte_q = models.Q(event_date__lte=upd_date)
            fraction_q = models.Q(host_golfclub__pk=host_club_id, region=region, division=division, section=section)
            #print "-", region, section, division, upd_date

            if LeaderBoard.objects.filter(date=upd_date).filter(fraction_q).count():
                # данные уже есть
                #print "LeaderBoard for %s already calculated" % upd_date
                #continue
                LeaderBoard.objects.filter(date=upd_date).filter(fraction_q).delete()

            #else:
            lb_obj = LeaderBoard.objects.create(date=upd_date, host_golfclub_id=host_club_id, region=region, division=division, section=section)

            player_ids = set(
                (v[0] for v in UpdateLine.objects.filter(fraction_q).filter(date_lte_q).values_list("player").distinct()))
            #print player_ids

            fraction_scores = {}

            # так, мне нужно получить на выходе таблицу

            for ln in UpdateLine.objects.select_related("home_golfclub").filter(fraction_q).filter(date_lte_q):
                if ln.player_id not in fraction_scores:
                    fraction_scores[ln.player_id] = []
                fraction_scores[ln.player_id].append(
                        {"date": ln.event_date, "result": ln.result, "handicap": ln.handicap,
                         "home club": ln.home_golfclub.name})


            #pprint(fraction_scores)
            for player_id in fraction_scores.keys():
                player_obj = Player.objects.get(pk=player_id)
                # счет последнего обновления
                latest_score = fraction_scores[player_id][-1]["result"]
                handicap_current = fraction_scores[player_id][-1]["handicap"]
                home_club = fraction_scores[player_id][-1]["home club"]

                # топы - 1st, 2nd, 3rd
                top_results = [ln.result for ln in
                               UpdateLine.objects.filter(fraction_q).filter(date_lte_q).filter(player=player_obj).order_by(
                                   "-result", "-event_date")[:3]]

                # playoff status
                playoff_status = "Q" if len(top_results) >= 3 else "N Q"
                while len(top_results) != 3:
                    top_results.append(0)

                # так, все данные кроме позиций и их движения у меня есть.

                # в принципе можно записать их в таблицу
                lb_line_obj = lb_obj.leaderboardline_set.create(
                    player=player_obj,
                    playoff_status=playoff_status,
                    latest_score=latest_score,
                    curr_handicap=handicap_current,
                    top_round_1st=top_results[0],
                    top_round_2nd=top_results[1],
                    top_round_3rd=top_results[2],
                )



def update_leaderboards_positions():
    # теперь нужно посчитать результаты для каждого лидерборда по сравнению с предыдущим.
    for host_club_id, region, section, division in UpdateLine.objects.all().values_list("host_golfclub", "region",
        "section", "division").distinct():
        fraction_q = models.Q(host_golfclub__pk=host_club_id, region=region, division=division, section=section)

        while True:
            # берем самый давний лидерборд, для которого не посчитан счет.
            print fraction_q
            oldest_nonscored_lb_objs = LeaderBoard.objects.filter(fraction_q).filter(scored_against=None).order_by("date")[0:1]
            if not oldest_nonscored_lb_objs:
                break
            oldest_nonscored_lb_obj = oldest_nonscored_lb_objs[0]
            print oldest_nonscored_lb_obj

            # проверяем, не первый ли он? т.е. есть ли что-то до него

            if not LeaderBoard.objects.filter(fraction_q).filter(date__lt=oldest_nonscored_lb_obj.date).count():
                # первый считаем по сравнению с им самим (т.е. никаких движений игроков там не будет)
                print "first detected"

                lb_obj_prev = oldest_nonscored_lb_obj
            else:
                lb_obj_prev = LeaderBoard.objects.filter(fraction_q).filter(date__lt=oldest_nonscored_lb_obj.date).order_by("-date").all()[0]


            # [25.04.2012 10:54:43] Ivan Nemytchenko:
            # 1) не смотря, что он NQ - у него  все равно есть какое-то место в таблице. Кстати сумма очков всегда делится на три, даже если была сыграна одна игра.
            # 2) Нет. Выводим средний балл с точностью до второго знака после запятой. если совпало у кого-то, то не паримся пока.

            for n, lb_ln_obj in enumerate(
                oldest_nonscored_lb_obj.leaderboardline_set.extra(
                    select={'sum_round': "-(top_round_1st+top_round_2nd+top_round_3rd)"}).order_by("sum_round")):

                if lb_obj_prev == oldest_nonscored_lb_obj:
                    prev_pos = 0
                else:
                    try:
                        prev_pos = lb_obj_prev.leaderboardline_set.get(player=lb_ln_obj.player).curr_position
                    except  LeaderBoardLine.DoesNotExist:
                        prev_pos = 0

                lb_ln_obj.prev_position = prev_pos
                lb_ln_obj.curr_position = n + 1
                lb_ln_obj.save()

            oldest_nonscored_lb_obj.scored_against = lb_obj_prev
            oldest_nonscored_lb_obj.save()



if __name__ == "__main__":

    csv_file_name = "data.csv"
    load_csv(csv_file_name)
    fill_leaderboards()
    update_leaderboards_positions()

