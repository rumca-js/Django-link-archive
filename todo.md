======================================================================
FAIL: test_write__daily_data__json (rsshistory.tests.test_datawriter.DataWriterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_datawriter.py", line 239, in test_write__daily_data__json
    self.assertEqual(len(json_obj), 2)
AssertionError: 1 != 2

======================================================================
FAIL: test_write__notime__json (rsshistory.tests.test_datawriter.DataWriterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_datawriter.py", line 203, in test_write__notime__json
    self.assertEqual(len(json_obj), 3)
AssertionError: 2 != 3

======================================================================
FAIL: test_write__notime__many_sources (rsshistory.tests.test_datawriter.DataWriterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_datawriter.py", line 288, in test_write__notime__many_sources
    self.assertEqual(len(json_obj), 3)
AssertionError: 2 != 3

======================================================================
FAIL: test_build_from_props__ipv4_accept (rsshistory.tests.test_entrydatabuilder.EntryDataBuilderTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_entrydatabuilder.py", line 359, in test_build_from_props__ipv4_accept
    self.assertEqual(objs.count(), 1)
AssertionError: 0 != 1

======================================================================
FAIL: test_build_from_props__no_slash (rsshistory.tests.test_entrydatabuilder.EntryDataBuilderTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_entrydatabuilder.py", line 67, in test_build_from_props__no_slash
    self.assertEqual(objs.count(), 1)
AssertionError: 0 != 1

======================================================================
FAIL: test_follow_url__youtube_channel (rsshistory.tests.test_feedclient.FeedClientTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_feedclient.py", line 105, in test_follow_url__youtube_channel
    self.assertEqual(number_of_source, 1)
AssertionError: 0 != 1

======================================================================
FAIL: test_rss_in_html (rsshistory.tests.test_internet_pages.InternetTest)
Warhammer community could not be read because rss was in html, and
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_internet_pages.py", line 29, in test_rss_in_html
    self.assertTrue(len(container_elements) > 0)
AssertionError: False is not true

======================================================================
FAIL: test_youtube_channel (rsshistory.tests.test_internet_pages.InternetTest)
YouTube channels are protected by cookie requests
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_internet_pages.py", line 61, in test_youtube_channel
    self.assertEqual(props["title"], "Linus Tech Tips")
AssertionError: None != 'Linus Tech Tips'

======================================================================
FAIL: test_import_from_data__all (rsshistory.tests.test_serializers_jsonimporter.JsonImporterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_serializers_jsonimporter.py", line 127, in test_import_from_data__all
    self.assertEqual(UserVotes.objects.all().count(), 1)
AssertionError: 0 != 1

======================================================================
FAIL: test_import_from_data__entries (rsshistory.tests.test_serializers_jsonimporter.JsonImporterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_serializers_jsonimporter.py", line 78, in test_import_from_data__entries
    self.assertEqual(UserTags.objects.all().count(), 0)
AssertionError: 2 != 0

======================================================================
FAIL: test_import_from_data__entries__strict (rsshistory.tests.test_serializers_jsonimporter.JsonImporterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_serializers_jsonimporter.py", line 103, in test_import_from_data__entries__strict
    self.assertEqual(UserTags.objects.all().count(), 0)
AssertionError: 2 != 0

======================================================================
FAIL: test_main_exporter__both (rsshistory.tests.test_serializers_mainexporter.MainExporterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_serializers_mainexporter.py", line 122, in test_main_exporter__both
    self.assertEqual(entries.count(), 2)
AssertionError: 3 != 2

======================================================================
FAIL: test_main_exporter__parmanents (rsshistory.tests.test_serializers_mainexporter.MainExporterTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_serializers_mainexporter.py", line 111, in test_main_exporter__parmanents
    self.assertEqual(entries.count(), 1)
AssertionError: 3 != 1

======================================================================
FAIL: test_is_props_valid (rsshistory.tests.test_sourceplugins_parse.HackerNewsParserPluginTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_sourceplugins_parse.py", line 132, in test_is_props_valid
    self.assertEqual(jobs.count(), len(props))
AssertionError: 0 != 20

======================================================================
FAIL: test_is_props_valid (rsshistory.tests.test_sourceplugins_parse.RssParserPluginTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_sourceplugins_parse.py", line 88, in test_is_props_valid
    self.assertTrue(jobs.count() > 0)
AssertionError: False is not true

======================================================================
FAIL: test_get_entries__encoded (rsshistory.tests.test_sourceplugins_rss.BaseRssPluginTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_sourceplugins_rss.py", line 128, in test_get_entries__encoded
    self.assertEqual(len(props), 5)
AssertionError: 0 != 5

======================================================================
FAIL: test_more_than_limit (rsshistory.tests.test_userhistory.UserSearchHistoryTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_userhistory.py", line 75, in test_more_than_limit
    self.assertEqual(objects.count(), limit)
AssertionError: 79 != 60

======================================================================
FAIL: test_entry_tag (rsshistory.tests.test_views_tags.UserTagsTest)
----------------------------------------------------------------------
Traceback (most recent call last):
  File "/home/hunter/WorkDir/test/linklibrary/rsshistory/tests/test_views_tags.py", line 74, in test_entry_tag
    self.assertEqual(jobs.count(), 1)
AssertionError: 0 != 1

----------------------------------------------------------------------
Ran 793 tests in 245.307s

FAILED (failures=18)
Destroying test database for alias 'default' ('file:memorydb_default?mode=memory&cache=shared')...
make: *** [Makefile:110: test] Błąd 1
hunter@hunter-System-Product-Name:~/WorkDir/test/linklibrary$ 


