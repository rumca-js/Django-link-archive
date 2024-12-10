https://relisten.net/
https://www.savethearchive.com/
https://modelcontextprotocol.io
places / tag dropbox as file hosting
catalog / add https://www.youtube.com/watch?v=xDm3zdkgBZ0
catalog / add https://www.youtube.com/watch?v=t3VWSMWOxwc
places / add https://github.com/home-assistant/operating-system



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

----------------------------------------------------------------------
Ran 793 tests in 245.307s
