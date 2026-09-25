import contextlib
import io
import unittest
from unittest.mock import patch
from normalizers.composite_signal import build_signal


class CompositeFreshnessTest(unittest.TestCase):
    def test_build_preserves_source_dates_and_unknown_metrics(self):
        payloads = [
            {'metadata': {'last_updated': '2026-09-24'}, 'monthly': [{'pct_of_m1': 0}]},
            {}, {}, {},
            {'metadata': {'last_updated': '2026-05-29'}, 'layers': [{'number': 5, 'status': 'unknown'}]},
            {}, {}, {},
        ]
        with patch('normalizers.composite_signal.load_json', side_effect=payloads), contextlib.redirect_stdout(io.StringIO()):
            result = build_signal('2026-09-25')
        self.assertEqual(result['metadata']['built_at'], '2026-09-25')
        self.assertEqual(result['metadata']['last_updated'], '2026-09-24')
        self.assertEqual(result['metadata']['source_dates']['adoption'], '2026-05-29')
        self.assertEqual(result['key_metrics']['supply_pct_of_m1'], 0)
        self.assertIsNone(result['key_metrics']['commercial_pct_of_ach'])
        self.assertEqual(result['layers_summary']['invisible'], 'unknown')
