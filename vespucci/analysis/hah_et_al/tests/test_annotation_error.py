'''
Created on Jun 9, 2013

@author: karmel

Sorry, world. These are functional tests.
'''
from io import StringIO
import unittest

import pandas

from vespucci.analysis.hah_et_al.annotation_error import TranscriptEvaluator
genes = '''chr1    100    200    +
chr1    300    500    +
chr1    600    700    -
chr1    600    800    -
chr2    300    500    +'''


class TranscriptEvaluatorTest(unittest.TestCase):
    evaluator = None

    def setUp(self):
        self.evaluator = TranscriptEvaluator()
        ref = pandas.read_csv(StringIO(genes), sep='    ', header=None)
        self.evaluator.set_reference(ref)
        super(TranscriptEvaluatorTest, self).setUp()

    def _get_count_broken(self, data_str):
        target = pandas.read_csv(StringIO(data_str), sep='    ', header=None)
        self.evaluator.set_target(target)
        return self.evaluator.count_broken_reference()

    def _get_count_run_together(self, data_str):
        target = pandas.read_csv(StringIO(data_str), sep='    ', header=None)
        self.evaluator.set_target(target)
        return self.evaluator.count_run_together_reference()

    def test_no_overlap(self):
        '''
        Neg control.
            [-------------------]
                                    [--------]
        '''
        data_str = 'chr1    800    900    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertFalse(self._get_count_run_together(data_str))

    def test_start_overlap(self):
        '''
        Neg control.
            [-------------------]
        [----------]
        '''
        data_str = 'chr1    50    150    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertFalse(self._get_count_run_together(data_str))

    def test_end_overlap(self):
        '''
        Neg control.
            [-------------------]
                        [------------]
        '''
        data_str = 'chr1    150    250    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertFalse(self._get_count_run_together(data_str))

    def test_gene_containment(self):
        '''
        Neg control.
            [-------------------]
        [---------------------------]
        '''
        data_str = 'chr1    50    250    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertFalse(self._get_count_run_together(data_str))

    def test_target_containment(self):
        '''
        Neg control.
            [-------------------]
                [-------------]
        '''
        data_str = 'chr1    125    175    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertFalse(self._get_count_run_together(data_str))

    def test_diff_strand(self):
        '''
        Neg control.
            [-------------------] +
        [-------------]   [-------------] -
        '''
        data_str = 'chr1    50    150    -'\
            + '\nchr1    175    250    -'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertFalse(self._get_count_run_together(data_str))

    def test_diff_chr(self):
        '''
        Neg control.
            [-------------------] 1
        [-------------]   [-------------] 2
        '''
        data_str = 'chr2    50    150    +'\
            + '\nchr2    175    250    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertFalse(self._get_count_run_together(data_str))

    def test_broken_overlap(self):
        '''
        Pos control.
            [-------------------]
        [-------------]   [-------------]
        '''
        data_str = 'chr1    50    150    +'\
            + '\nchr1    175    250    +'
        self.assertEqual(self._get_count_broken(data_str), 1)
        self.assertFalse(self._get_count_run_together(data_str))

    def test_broken_contained(self):
        '''
        Pos control.
            [-------------------]
            [------]   [------]
        '''
        data_str = 'chr1    100    125    +'\
            + '\nchr1    150    175    +'
        self.assertEqual(self._get_count_broken(data_str), 1)
        self.assertFalse(self._get_count_run_together(data_str))

    def test_many_broken(self):
        '''
        Pos control.
            [-------------------]
        [-------] [----] [-------------]
        '''
        data_str = 'chr1    50    125    +'\
            + '\nchr1    130    150    +'\
            + '\nchr1    175    250    +'
        self.assertEqual(self._get_count_broken(data_str), 1)
        self.assertFalse(self._get_count_run_together(data_str))

    def test_broken_boundary(self):
        '''
        Pos control.
            [-------------------]
        [---]                   [------]
        '''
        data_str = 'chr1    50    100    +'\
            + '\nchr1    200    250    +'
        self.assertEqual(self._get_count_broken(data_str), 1)
        self.assertFalse(self._get_count_run_together(data_str))

    def test_run_together_overlap(self):
        '''
        Pos control.
            [--------]             [--------]
                [-------------------------]
        '''
        data_str = 'chr1    150    350    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertEqual(self._get_count_run_together(data_str), 1)

    def test_run_together_contained(self):
        '''
        Pos control.
            [--------] [--------]
        [-------------------------------]
        '''
        data_str = 'chr1    50    550    +'
        self.assertFalse(self._get_count_broken(data_str))
        self.assertEqual(self._get_count_run_together(data_str), 1)

    def test_broken_isoforms(self):
        '''
        Pos control.
            [---------------]
            [-------------------]
        [-------------]   [-------------]
        '''
        data_str = 'chr1    550    650    -'\
            + '\nchr1    675    850    -'
        self.assertEqual(self._get_count_broken(data_str), 2)
        self.assertFalse(self._get_count_run_together(data_str))


if __name__ == '__main__':
    unittest.main()
