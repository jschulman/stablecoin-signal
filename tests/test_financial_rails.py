import copy
import json
import unittest
from datetime import date
from pathlib import Path
from normalizers.financial_rails import build_summary, validate

ROOT = Path(__file__).resolve().parents[1]


class FinancialRailsTest(unittest.TestCase):
    def setUp(self):
        self.data = json.loads((ROOT / 'data/rails/evidence.json').read_text())
        self.today = date(2026, 9, 25)

    def test_curated_mirror_and_conservative_stages(self):
        self.assertEqual(self.data, json.loads((ROOT / 'docs/data/rails/evidence.json').read_text()))
        result = build_summary(self.data, self.today)
        self.assertEqual(result['summary']['stage_counts']['limited-production'], 2)
        self.assertEqual(result['summary']['recurring_records'], 0)
        self.assertNotIn('total_volume', result['summary'])

    def test_announced_does_not_become_production_with_time(self):
        record = self.data['records'][0]
        record['stage'] = 'announced'
        record['stage_evidence']['production_observed'] = False
        result = build_summary(self.data, date(2027, 10, 1))
        self.assertEqual(result['records'][1]['stage'], 'announced')

    def test_invalid_production_claim(self):
        self.data['records'][0]['stage_evidence']['production_observed'] = False
        with self.assertRaisesRegex(ValueError, 'Production stage'):
            validate(self.data, self.today)

    def test_recurring_requires_evidence_of_repeat_activity(self):
        self.data['records'][0]['stage'] = 'recurring-production'
        with self.assertRaisesRegex(ValueError, 'documented repeat'):
            validate(self.data, self.today)
        recurring = self.data['records'][0]['recurring_evidence']
        recurring.update(status='documented', source_ids=['visa-2025-12-16'], observation_dates=['2025-12-16'])
        with self.assertRaisesRegex(ValueError, 'two distinct'):
            validate(self.data, self.today)

    def test_unknown_is_null_and_measured_zero_is_preserved(self):
        result = build_summary(self.data, self.today)
        self.assertTrue(all(r['volume']['value'] is None for r in result['records']))
        record = self.data['records'][0]
        record['volume'].update(value=0, unit='USD', period='2025-12-16', source_ids=['visa-2025-12-16'])
        result = build_summary(self.data, self.today)
        self.assertEqual(result['summary']['unknown_volume_records'], 1)
        self.assertEqual(result['records'][1]['volume']['value'], 0)

    def test_null_is_explicit_and_bool_is_not_volume(self):
        del self.data['records'][0]['volume']['value']
        with self.assertRaisesRegex(ValueError, 'expected fields'):
            validate(self.data, self.today)
        self.data['records'][0]['volume']['value'] = True
        self.data['records'][0]['volume']['source_ids'] = ['visa-2025-12-16']
        with self.assertRaisesRegex(ValueError, 'finite nonnegative'):
            validate(self.data, self.today)

    def test_review_expiry_does_not_refresh_source(self):
        result = build_summary(self.data, date(2026, 10, 26))
        self.assertEqual(result['summary']['overdue_reviews'], 2)
        self.assertEqual(result['metadata']['built_at'], '2026-10-26')
        self.assertEqual(result['metadata']['latest_source_date'], '2026-07-15')
        self.assertEqual(result['records'][1]['reviewed_at'], '2026-09-25')
        self.assertGreater(result['records'][1]['source_age_days'], 300)
        boundary = build_summary(self.data, date(2026, 10, 25))
        self.assertEqual(boundary['summary']['overdue_reviews'], 0)

    def test_duplicate_event_rejected_across_categories(self):
        duplicate = copy.deepcopy(self.data['records'][0])
        duplicate.update(id='duplicate', category='institutional-treasury')
        self.data['records'].append(duplicate)
        with self.assertRaisesRegex(ValueError, 'Duplicate event'):
            validate(self.data, self.today)

    def test_schema_rejects_invalid_dates_sources_and_enums(self):
        changes = [('stage', 'mainstream'), ('reviewed_at', '2026-10-01'), ('event_date', 'yesterday')]
        for key, value in changes:
            with self.subTest(key=key):
                data = copy.deepcopy(self.data)
                data['records'][0][key] = value
                with self.assertRaises(ValueError):
                    validate(data, self.today)
        self.data['records'][0]['stage_evidence']['source_ids'] = ['not-a-source']
        with self.assertRaisesRegex(ValueError, 'unknown source reference'):
            validate(self.data, self.today)

    def test_deterministic_and_does_not_mutate_source(self):
        original = copy.deepcopy(self.data)
        first = build_summary(self.data, self.today)
        self.assertEqual(first, build_summary(self.data, self.today))
        self.assertEqual(original, self.data)

    def test_consumer_dates_and_correction_stay_scoped(self):
        adoption = json.loads((ROOT / 'data/adoption/layers.json').read_text())
        self.assertEqual(adoption['metadata']['last_updated'], '2026-05-29')
        self.assertEqual(len(adoption['layers']), 5)
        invisible = next(r for r in adoption['layers'] if r['number'] == 5)
        self.assertEqual(invisible['status'], 'unknown')
        self.assertEqual(invisible['source_date'], '2025-12-16')


if __name__ == '__main__':
    unittest.main()
