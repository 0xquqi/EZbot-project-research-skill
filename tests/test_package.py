import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('package_check', ROOT / 'tools/check.py')
m = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(m)


class EvidenceBoundaryTests(unittest.TestCase):
    def setUp(self):
        refs = ROOT / 'skills/ezbot-project-research/references'
        self.cards = json.loads((refs / 'question-cards.json').read_text())['rules']
        self.sources = {s['id']: s for s in json.loads((refs / 'source-catalog.json').read_text())['sources']}

    def test_actual_topics_have_read_primary_basis(self):
        m.validate_cards(self.cards, self.sources)

    def test_missing_provenance_is_rejected(self):
        del self.cards[0]['source_ids']
        with self.assertRaises(ValueError):
            m.validate_cards(self.cards, self.sources)

    def test_an_unread_source_does_not_support_a_topic(self):
        key = self.cards[0]['source_ids'][0]
        self.sources[key]['status'] = 'unavailable'
        with self.assertRaises(ValueError):
            m.validate_cards(self.cards, self.sources)

    def test_no_read_to_execution_upgrade(self):
        self.cards[0]['execution_tested'] = True
        with self.assertRaises(ValueError):
            m.validate_cards(self.cards, self.sources)

    def test_no_general_card_inherits_target_address(self):
        self.cards[0]['questions'].append('Use ' + '0x' + '1'*40)
        with self.assertRaises(ValueError):
            m.validate_cards(self.cards, self.sources)

    def test_method_without_procedure_is_rejected(self):
        self.cards[0]['procedure'] = []
        with self.assertRaises(ValueError):
            m.validate_cards(self.cards, self.sources)

    def test_failed_read_cannot_count_as_retrieved_material(self):
        refs = ROOT / 'skills/ezbot-project-research/references'
        studies = json.loads((refs / 'activity-studies.json').read_text())
        ledger = json.loads((refs / 'ecology-review.json').read_text())
        ledger['counts']['retrieved_materials'] = 40
        with self.assertRaisesRegex(ValueError, 'Failed read'):
            m.validate_review(studies, ledger, self.cards, self.sources)

    def test_new_review_cannot_become_recovered_history(self):
        refs = ROOT / 'skills/ezbot-project-research/references'
        studies = json.loads((refs / 'activity-studies.json').read_text())
        ledger = json.loads((refs / 'ecology-review.json').read_text())
        ledger['historical_40_index_recovered'] = True
        with self.assertRaisesRegex(ValueError, 'historical evidence'):
            m.validate_review(studies, ledger, self.cards, self.sources)

    def test_real_rpc_errors_are_preserved(self):
        o = json.loads((ROOT / 'evaluation/observations-2026-10-28.json').read_text())
        self.assertTrue(o['rpc']['fixed_block_attempts'])
        self.assertTrue(all(r['error'] for r in o['rpc']['fixed_block_attempts']))
        self.assertFalse(o['rpc']['drawPrice_latest']['pinned_to_recorded_block'])
        self.assertFalse(o['browser']['wallet_connected'])


if __name__ == '__main__':
    unittest.main()
