from datetime import datetime, date, timedelta

from django.db import models
from django.urls import reverse
from django.templatetags.static import static
import django.utils


class KeyWords(models.Model):
    keyword = models.CharField(max_length=200)
    language = models.CharField(max_length=10, default="en")
    date_published = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_published"]

    def count(keyword):
        keys = KeyWords.objects.filter(keyword=keyword)
        return keys.count()

    def is_valid(str_token):
        # check if non alphanumeric?
        if (
            str_token.find("<") >= 0
            or str_token.find(">") >= 0
            or str_token.find("=") >= 0
            or str_token.find("/") >= 0
            or str_token.find(";") >= 0
            or str_token.find('"') >= 0
            or str_token.find("#") >= 0
            or str_token.find("+") >= 0
            or str_token.find("?") >= 0
            or str_token.find("&amp;") >= 0
        ):
            return False

        if len(str_token) == 1:
            return False

        return True

    def is_common(str_token):
        if (
            str_token == "day"
            or str_token == "days"
            or str_token == "month"
            or str_token == "months"
            or str_token == "year"
            or str_token == "years"
            or str_token == "world"
            or str_token == "news"
            or str_token == "week"
            or str_token == "today"
            or str_token == "comments"
            or str_token == "january"
            or str_token == "february"
            or str_token == "march"
            or str_token == "april"
            or str_token == "june"
            or str_token == "july"
            or str_token == "september"
            or str_token == "october"
            or str_token == "november"
            or str_token == "decmber"
            or str_token == "monday"
            or str_token == "tuesday"
            or str_token == "wednesday"
            or str_token == "thursday"
            or str_token == "friday"
            or str_token == "saturday"
            or str_token == "sunday"
            or str_token == "cnet"
            or str_token == "new"
        ):
            return True
        return False

    def load_token_program(language):
        try:
            import spacy

            if language.find("en") >= 0:
                load_text = "en_core_web_sm"
            elif language.find("pl") >= 0:
                load_text = "pl_core_news_sm"
            else:
                return

            return spacy.load(load_text)
        except Exception as E:
            return

    def add_text(text, language):
        if not language:
            return
            
        if language == "":
            language = "en"
        
        if language.find("en") == -1:
            return

        nlp = KeyWords.load_token_program(language)
        if not nlp:
            return

        doc = nlp(text)

        # insert one occurance for the text
        # should limit spamming words
        important_tokens = set()

        for token in doc:
            # some words may appear in the beginning of the sentence -
            # lets ignore case entirely
            str_token = str(token).lower()
            if not KeyWords.is_valid(str_token):
                continue
            if KeyWords.is_common(str_token):
                continue

            # print("keyword:{} type:{}".format(str_token, token.pos_))

            if token.pos_ == "NOUN" or token.pos_ == "PROPN":
                important_tokens.add(str_token)

        for str_token in important_tokens:
            KeyWords.objects.create(keyword=str_token, language=language)

    def add_link_data(link_data):
        from ..configuration import Configuration

        if Configuration.get_object().config_entry.auto_store_keyword_info:
            if "language" not in link_data:
                return False

            if "date_published" not in link_data:
                return False

            if not KeyWords.is_keyword_date_range(link_data["date_published"]):
                return False

            # TODO we should make some switch in sources if it should store keywords
            if link_data["link"].find("www.reddit.com") != -1:
                return False

            # duplicate words are not counted. We joint title and description
            # for the words to be counted once only
            keyworded_text = link_data["title"]
            KeyWords.add_text(keyworded_text, link_data["language"])

            return True

    def clear():
        from ..dateutils import DateUtils

        # entries older than 2 days
        date_before_limit = KeyWords.get_keywords_date_limit()
        keys = KeyWords.objects.filter(date_published__lt=date_before_limit)
        keys.delete()

        ## Each day capture new keywords
        # keys = KeyWords.objects.all()
        # keys.delete()

    def get_keywords_date_limit():
        from ..dateutils import DateUtils

        return DateUtils.get_days_before_dt(1)

    def get_keyword_data(day_iso=None):
        # collect how many times keyword exist
        counter = {}

        if day_iso is None:
            keys = KeyWords.objects.all()
        else:
            date_range = DateUtils.get_range4day(day_iso)
            keys = KeyWords.objects.filter(date_published__range=date_range)

        for key in keys:
            if key.keyword in counter:
                counter[key.keyword] += 1
            else:
                counter[key.keyword] = 1

        # transform to list
        content_list = []
        for key in counter:
            value = counter[key]
            # content_list.append([key, value])

            if value > 1:
                content_list.append([key, value])

        # sort
        content_list = sorted(content_list, key=lambda x: (x[1], x[0]), reverse=True)
        return content_list

    def is_keyword_date_range(input_date):
        # TODO we clear every beginning of
        # maybe we should clear
        from ..dateutils import DateUtils
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry

        date_limit = KeyWords.get_keywords_date_limit()
        if input_date < date_limit:
            return False
        return True
