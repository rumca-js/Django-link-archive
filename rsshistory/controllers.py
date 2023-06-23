from datetime import datetime, timedelta

from django.db.models import Q

from .models import LinkCommentDataModel

class LinkCommentDataController(object):
    def __init__(self, comment):
        pass

    def can_user_add_comment(user_name):
        now = datetime.now()
        time_start = now - timedelta(days = 1)
        time_stop = now

        criterion0 = Q(author=user_name)
        criterion1 = Q(date_published__range=[time_start, time_stop])
        criterion2 = Q(date_edited__range=[time_start, time_stop])

        comments = LinkCommentDataModel.objects.filter(criterion0 & (criterion1 | criterion2))
        if len(comments) > 0:
            return False

        return True
