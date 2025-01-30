from datetime import datetime, date, timedelta

from django.db import models
from django.urls import reverse
from django.templatetags.static import static

from utils.dateutils import DateUtils

from .system import AppLogging, ConfigurationEntry


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

    def is_configuration_error():
        if not ConfigurationEntry.get().enable_keyword_support:
            return False

        from ..configuration import Configuration

        if Configuration.get_object().get_nlp("en") is None:
            return False

        # TODO this kind of is slow, breaks browser speed
        # if KeyWords.load_token_program("en") is None:
        #    return True

        return True

    def add_text(text, language):
        from ..configuration import Configuration

        if not language:
            return

        if language == "":
            language = "en"

        if language.find("en") == -1:
            return

        nlp = Configuration.get_object().get_nlp(language)
        if not nlp:
            AppLogging.error(
                "Cannot load token program for language:{}".format(language)
            )
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

            if token.pos_ == "NOUN" or token.pos_ == "PROPN":
                important_tokens.add(str_token)

        for str_token in important_tokens:
            KeyWords.objects.create(keyword=str_token, language=language)

    def add_link_data(link_data):
        from ..configuration import Configuration

        if Configuration.get_object().config_entry.enable_keyword_support:
            if "language" not in link_data:
                return False

            if "date_published" not in link_data:
                return False

            if not KeyWords.is_keyword_date_range(link_data["date_published"]):
                return False

            # duplicate words are not counted. We joint title and description
            # for the words to be counted once only
            keyworded_text = link_data["title"]
            KeyWords.add_text(keyworded_text, link_data["language"])

            return True

    def cleanup(cfg=None):
        from ..configuration import Configuration

        if Configuration.get_object().config_entry.enable_keyword_support:
            date_before_limit = KeyWords.get_keywords_date_limit()
            keys = KeyWords.objects.filter(date_published__lt=date_before_limit)
            keys.delete()
        else:
            keys = KeyWords.objects.all()
            keys.delete()

    def get_keywords_date_limit():
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
        from ..configuration import Configuration

        conf = Configuration.get_object().config_entry

        date_limit = KeyWords.get_keywords_date_limit()
        if input_date < date_limit:
            return False
        return True
