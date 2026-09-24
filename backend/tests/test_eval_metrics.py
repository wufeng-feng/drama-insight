import unittest

from evals.run_eval import match_events


class MatchEventsTest(unittest.TestCase):
    def test_exact_matches_have_perfect_scores(self):
        predictions = [
            {"type": "opening_hook", "start_time": 1},
            {"type": "climax", "start_time": 40},
        ]
        truth = [
            {"type": "opening_hook", "start_time": 0},
            {"type": "climax", "start_time": 42},
        ]

        counts = match_events(predictions, truth, time_tolerance=5)

        self.assertEqual(counts.true_positive, 2)
        self.assertEqual(counts.false_positive, 0)
        self.assertEqual(counts.false_negative, 0)
        self.assertEqual(counts.f1, 1.0)

    def test_prediction_can_only_match_one_truth_item(self):
        predictions = [{"type": "conflict", "start_time": 10}]
        truth = [
            {"type": "conflict", "start_time": 9},
            {"type": "conflict", "start_time": 11},
        ]

        counts = match_events(predictions, truth, time_tolerance=5)

        self.assertEqual(counts.true_positive, 1)
        self.assertEqual(counts.false_positive, 0)
        self.assertEqual(counts.false_negative, 1)

    def test_wrong_type_is_not_a_match(self):
        predictions = [{"type": "climax", "start_time": 10}]
        truth = [{"type": "conflict", "start_time": 10}]

        counts = match_events(predictions, truth)

        self.assertEqual(counts.true_positive, 0)
        self.assertEqual(counts.false_positive, 1)
        self.assertEqual(counts.false_negative, 1)


if __name__ == "__main__":
    unittest.main()
