from pathlib import Path


def replace_exact(path: str, old: str, new: str) -> None:
    file = Path(path)
    text = file.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one match, found {count}: {old[:120]!r}")
    file.write_text(text.replace(old, new))


replace_exact(
    "backend/diabetes/services/clinical/proactive_attention.py",
    '''    if observation.status == ClinicalObservationState.STATUS_INACTIVE:\n        if _resolution_criterion_met(\n            observation,\n            dataset_eligible=dataset_eligible,\n            now=now,\n        ):\n            return ClinicalInsightState.STATE_RESOLVED\n        if not dataset_eligible:\n            return insight.lifecycle_state\n        return ClinicalInsightState.STATE_MONITORING\n\n    if created:\n        return ClinicalInsightState.STATE_NEW\n''',
    '''    # Fresh data insufficiency may change the allowed next step, but it may not\n    # strengthen or resolve clinical-attention lifecycle state. Preserve any known\n    # state; a newly initialized historical observation starts in MONITORING.\n    if not dataset_eligible:\n        return (\n            ClinicalInsightState.STATE_MONITORING\n            if created\n            else insight.lifecycle_state\n        )\n\n    if observation.status == ClinicalObservationState.STATUS_INACTIVE:\n        if _resolution_criterion_met(\n            observation,\n            dataset_eligible=dataset_eligible,\n            now=now,\n        ):\n            return ClinicalInsightState.STATE_RESOLVED\n        return ClinicalInsightState.STATE_MONITORING\n\n    if created:\n        return ClinicalInsightState.STATE_NEW\n''',
)

replace_exact(
    "backend/diabetes/services/clinical/proactive_attention.py",
    '''    if _moves_toward_recorded_baseline(observation):\n        return ClinicalInsightState.STATE_IMPROVING\n\n    if observation.recurrence_count >= 2:\n        return ClinicalInsightState.STATE_PERSISTING\n\n    return ClinicalInsightState.STATE_MONITORING\n''',
    '''    # A repeated activation is the stronger longitudinal fact. Baseline movement\n    # remains available in reason codes, but cannot relabel recurrence as improvement.\n    if observation.recurrence_count >= 2:\n        return ClinicalInsightState.STATE_PERSISTING\n\n    if _moves_toward_recorded_baseline(observation):\n        return ClinicalInsightState.STATE_IMPROVING\n\n    return ClinicalInsightState.STATE_MONITORING\n''',
)

replace_exact(
    "backend/diabetes/services/clinical/proactive_attention.py",
    '''    if created:\n        if observation.status == ClinicalObservationState.STATUS_ACTIVE:\n            return ["first_eligible_observation"]\n        return ["existing_observation_initialized"]\n''',
    '''    if created:\n        if not dataset_eligible:\n            return ["existing_observation_initialized", "current_data_insufficient"]\n        if observation.status == ClinicalObservationState.STATUS_ACTIVE:\n            return ["first_eligible_observation"]\n        return ["existing_observation_initialized"]\n''',
)

# Add two regression tests before the existing patient-scope test.
replace_exact(
    "backend/diabetes/tests/test_p2_proactive_attention.py",
    '''    def test_patient_scope_is_strict(self):\n''',
    '''    def test_insufficient_data_cannot_promote_existing_lifecycle(self):\n        supporting = self._stress_pattern(values=(200, 210, 220))\n        background = self._neutral_background(values=(100, 110, 120))\n        self._clear()\n\n        source = ClinicalObservationState.objects.get(\n            patient=self.patient,\n            observation_key="context:stress",\n        )\n        state = ClinicalInsightState.objects.get(observation=source)\n        self.assertEqual(state.lifecycle_state, ClinicalInsightState.STATE_MONITORING)\n\n        # Simulate already-known historical recurrence/baseline evolution. The fresh\n        # dataset then becomes insufficient. Neither stale signal may promote the\n        # proactive lifecycle during that insufficient refresh.\n        ClinicalObservationState.objects.filter(pk=source.pk).update(\n            recurrence_count=2,\n            previous_baseline_delta_mg_dl=50.0,\n            baseline_delta_mg_dl=20.0,\n            baseline_delta_change_mg_dl=-30.0,\n        )\n        ClinicalInsightState.objects.filter(pk=state.pk).update(\n            recurrence_count_snapshot=2,\n            baseline_delta_snapshot_mg_dl=20.0,\n        )\n        LogEntry.objects.filter(\n            pk__in=[entry.pk for entry in supporting + background]\n        ).update(logged_at=self.now - timedelta(days=100))\n\n        sparse = self._clear()\n        state.refresh_from_db()\n\n        self.assertIsNotNone(sparse.candidate)\n        assert sparse.candidate is not None\n        self.assertEqual(\n            sparse.candidate.allowed_next_step,\n            ClinicalInsightState.ACTION_COLLECT_MISSING_DATA,\n        )\n        self.assertEqual(sparse.candidate.lifecycle_state, ClinicalInsightState.STATE_MONITORING)\n        self.assertEqual(state.lifecycle_state, ClinicalInsightState.STATE_MONITORING)\n        self.assertNotEqual(state.lifecycle_state, ClinicalInsightState.STATE_PERSISTING)\n        self.assertNotEqual(state.lifecycle_state, ClinicalInsightState.STATE_IMPROVING)\n\n    def test_reactivation_dominates_simultaneous_baseline_improvement(self):\n        supporting = self._stress_pattern(values=(200, 210, 220))\n        self._neutral_background(values=(100, 110, 120))\n        self._clear()\n\n        source = ClinicalObservationState.objects.get(\n            patient=self.patient,\n            observation_key="context:stress",\n        )\n        original_delta = source.baseline_delta_mg_dl\n\n        LogEntry.objects.filter(pk__in=[entry.pk for entry in supporting]).update(\n            logged_at=self.now - timedelta(days=100)\n        )\n        self._clear()\n        source.refresh_from_db()\n        self.assertEqual(source.status, ClinicalObservationState.STATUS_INACTIVE)\n\n        for day, glucose in ((7, 130), (8, 140), (9, 150)):\n            self._log(days_ago=day, glucose=glucose, stressed="yes")\n\n        reactivated = self._clear()\n        source.refresh_from_db()\n\n        self.assertIsNotNone(reactivated.candidate)\n        assert reactivated.candidate is not None\n        self.assertEqual(source.recurrence_count, 2)\n        self.assertLess(abs(source.baseline_delta_mg_dl), abs(original_delta))\n        self.assertEqual(\n            reactivated.candidate.lifecycle_state,\n            ClinicalInsightState.STATE_PERSISTING,\n        )\n        self.assertIn("observation_reactivated", reactivated.candidate.what_changed)\n        self.assertIn("activation_episode_recurred", reactivated.candidate.what_changed)\n        self.assertIn("moved_toward_recorded_baseline", reactivated.candidate.what_changed)\n\n    def test_patient_scope_is_strict(self):\n''',
)
