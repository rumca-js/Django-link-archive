
from ..serializers.converters import PageSystem

from .fakeinternet import FakeInternetTestCase


class PageSystemPageTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_1(self):
        s = PageSystem(0, 1000)
        self.assertEqual(s.no_pages, 0)

    def test_2(self):
        s = PageSystem(1, 1000)
        self.assertEqual(s.no_pages, 1)

    def test_3(self):
        s = PageSystem(999, 1000)
        self.assertEqual(s.no_pages, 1)

    def test_4(self):
        s = PageSystem(1000, 1000)
        self.assertEqual(s.no_pages, 1)

    def test_5(self):
        s = PageSystem(1001, 1000)
        self.assertEqual(s.no_pages, 2)

    def test_6(self):
        s = PageSystem(1999, 1000)
        self.assertEqual(s.no_pages, 2)

    def test_7(self):
        s = PageSystem(2000, 1000)
        self.assertEqual(s.no_pages, 2)

    def test_8(self):
        s = PageSystem(2001, 1000)
        self.assertEqual(s.no_pages, 3)


class PageSystemSliceRangeTest(FakeInternetTestCase):
    def setUp(self):
        self.disable_web_pages()

    def test_1(self):
        s = PageSystem(0, 1000)
        limit = s.get_slice_limits(0)
        self.assertTrue(limit == None)

    def test_2(self):
        s = PageSystem(1, 1000)
        limit = s.get_slice_limits(0)
        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 1)

    def test_3(self):
        s = PageSystem(999, 1000)
        limit = s.get_slice_limits(0)
        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 999)

    def test_4(self):
        s = PageSystem(1000, 1000)
        limit = s.get_slice_limits(0)
        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 1000)

    def test_5(self):
        s = PageSystem(1001, 1000)
        limit = s.get_slice_limits(0)
        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 1000)

        limit = s.get_slice_limits(1)
        self.assertEqual(limit[0], 1000)
        self.assertEqual(limit[1], 1001)

    def test_6(self):
        s = PageSystem(1999, 1000)
        limit = s.get_slice_limits(0)
        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 1000)

        limit = s.get_slice_limits(1)
        self.assertEqual(limit[0], 1000)
        self.assertEqual(limit[1], 1999)

    def test_7(self):
        s = PageSystem(2000, 1000)

        limit = s.get_slice_limits(0)
        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 1000)

        limit = s.get_slice_limits(1)
        self.assertEqual(limit[0], 1000)
        self.assertEqual(limit[1], 2000)

    def test_8(self):
        s = PageSystem(2001, 1000)

        limit = s.get_slice_limits(0)
        self.assertEqual(limit[0], 0)
        self.assertEqual(limit[1], 1000)

        limit = s.get_slice_limits(1)
        self.assertEqual(limit[0], 1000)
        self.assertEqual(limit[1], 2000)

        limit = s.get_slice_limits(2)
        self.assertEqual(limit[0], 2000)
        self.assertEqual(limit[1], 2001)
