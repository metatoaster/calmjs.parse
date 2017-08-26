# -*- coding: utf-8 -*-
import unittest

from calmjs.parse import vlq


class VLQTestCase(unittest.TestCase):

    def test_vlq_encode_basic(self):
        self.assertEqual(vlq.encode_vlq(0), 'A')
        self.assertEqual(vlq.encode_vlq(1), 'C')
        self.assertEqual(vlq.encode_vlq(-1), 'D')
        self.assertEqual(vlq.encode_vlq(2), 'E')
        self.assertEqual(vlq.encode_vlq(-2), 'F')

    def test_vlq_encode_edge(self):
        self.assertEqual(vlq.encode_vlq(15), 'e')
        self.assertEqual(vlq.encode_vlq(-15), 'f')
        self.assertEqual(vlq.encode_vlq(16), 'gB')
        self.assertEqual(vlq.encode_vlq(-16), 'hB')
        self.assertEqual(vlq.encode_vlq(511), '+f')
        self.assertEqual(vlq.encode_vlq(-511), '/f')
        self.assertEqual(vlq.encode_vlq(512), 'ggB')
        self.assertEqual(vlq.encode_vlq(-512), 'hgB')

    def test_vlq_encode_multi(self):
        self.assertEqual(vlq.encode_vlq(456), 'wc')
        self.assertEqual(vlq.encode_vlq(-456), 'xc')
        self.assertEqual(vlq.encode_vlq(789), 'qxB')
        self.assertEqual(vlq.encode_vlq(-789), 'rxB')

    def test_encode_vlqs(self):
        self.assertEqual(vlq.encode_vlqs((0, 1, 2, 3, 4)), 'ACEGI')
        self.assertEqual(vlq.encode_vlqs((123, 456, 789)), '2HwcqxB')

    def test_decode_vlqs(self):
        self.assertEqual((0, 1, 2, 3, 4), vlq.decode_vlqs('ACEGI'))
        self.assertEqual((123, 456, 789), vlq.decode_vlqs('2HwcqxB'))

    def test_encode_mappings(self):
        self.assertEqual(vlq.encode_mappings([
            [(0, 0, 0, 0,), (6, 0, 0, 6,), (6, 0, 0, 6,)],
            []
        ]), 'AAAA,MAAM,MAAM;')

        self.assertEqual(vlq.encode_mappings([
            [(0, 0, 0, 0,)],
            [(0, 0, 1, 0,)],
            [(0, 0, 1, 0,)],
            []
        ]), 'AAAA;AACA;AACA;')

        self.assertEqual(vlq.encode_mappings([
            [],
            [],
            [(0, 0, 0, 0,), (6, 0, 0, 6,), (6, 0, 0, 6,)],
            [(8, 0, 0, 0,)],
            [],
            [(8, 0, 2, 0,)],
            [(8, 0, 1, 0,)],
            [(8, 0, 1, 0,)],
            [],
            [],
        ]), ';;AAAA,MAAM,MAAM;QAAA;;QAEA;QACA;QACA;;')

    def test_decode_mappings(self):
        self.assertEqual([
            [(0, 0, 0, 0,), (6, 0, 0, 6,), (6, 0, 0, 6,)],
            []
        ], vlq.decode_mappings('AAAA,MAAM,MAAM;'))

        self.assertEqual([
            [(0, 0, 0, 0,)],
            [(0, 0, 1, 0,)],
            [(0, 0, 1, 0,)],
            []
        ], vlq.decode_mappings('AAAA;AACA;AACA;'))

        self.assertEqual([
            [],
            [],
            [(0, 0, 0, 0,), (6, 0, 0, 6,), (6, 0, 0, 6,)],
            [(8, 0, 0, 0,)],
            [],
            [(8, 0, 2, 0,)],
            [(8, 0, 1, 0,)],
            [(8, 0, 1, 0,)],
            [],
            [],
        ], vlq.decode_mappings(';;AAAA,MAAM,MAAM;QAAA;;QAEA;QACA;QACA;;'))

    def test_create_sourcemap(self):
        sourcemap = vlq.create_sourcemap(
            'hello.min.js', [
                [(0, 0, 0, 0,), (6, 0, 0, 6,), (6, 0, 0, 6,)],
                []
            ], ['hello.js'], [],
        )
        self.assertEqual(sourcemap, {
            "version": 3,
            "sources": ["hello.js"],
            "names": [],
            "mappings": "AAAA,MAAM,MAAM;",
            "file": "hello.min.js"
        })
