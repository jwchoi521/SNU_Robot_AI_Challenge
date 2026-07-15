import unittest

from robot_nav_stack.track_evidence import TrackEvidence


class TrackEvidenceTest(unittest.TestCase):
    def test_same_frame_counts_once_and_keeps_highest_confidence(self) -> None:
        evidence = TrackEvidence()

        self.assertTrue(evidence.observe(10.0, "cube", "obstacle", 0.60))
        self.assertFalse(evidence.observe(10.0, "octahedron", "target", 0.55))
        self.assertTrue(evidence.observe(10.0, "octahedron", "target", 0.82))

        self.assertEqual(evidence.frame_count, 1)
        self.assertEqual(evidence.representative_class, "octahedron")
        self.assertEqual(evidence.representative_role, "target")
        self.assertEqual(evidence.class_scores, {"octahedron": 0.82})

    def test_three_distinct_frames_accumulate_class_confidence(self) -> None:
        evidence = TrackEvidence()

        evidence.observe(10.0, "octahedron", "target", 0.72)
        evidence.observe(10.5, "cube", "obstacle", 0.80)
        evidence.observe(11.0, "octahedron", "target", 0.70)

        self.assertEqual(evidence.frame_count, 3)
        self.assertEqual(evidence.representative_class, "octahedron")
        self.assertEqual(evidence.representative_role, "target")
        self.assertEqual(
            evidence.class_scores,
            {"octahedron": 1.42, "cube": 0.80},
        )

    def test_separate_tracks_count_the_same_frame_independently(self) -> None:
        left_track = TrackEvidence()
        right_track = TrackEvidence()

        left_track.observe(10.0, "octahedron", "target", 0.75)
        right_track.observe(10.0, "octahedron", "target", 0.78)

        self.assertEqual(left_track.frame_count, 1)
        self.assertEqual(right_track.frame_count, 1)


if __name__ == "__main__":
    unittest.main()
