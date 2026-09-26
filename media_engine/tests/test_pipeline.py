from pathlib import Path
from harmony360_media.orchestrator import MediaOrchestrator
from harmony360_media.agents import PublicationGate, YouTubeAdapter, MediaLedger


def build_episode(tmp_path):
    orch = MediaOrchestrator(memory_dir=tmp_path / 'ledger')
    return orch.create_episode(
        episode_id='H360-YT-EP001',
        series='Harmony360: Building the Framework',
        topic='Why PASS Does Not Mean Proof',
        sources=[{
            'source_id': 'SRC-001',
            'title': 'Harmony360 Core v1.0 Specification',
            'source_type': 'governed_document',
            'classification': 'UNDER_REVIEW',
        }],
        claims=[{
            'claim_id': 'CLAIM-001',
            'statement': 'A PASS means the defined test criteria were satisfied.',
            'claim_class': 'implemented',
            'status': 'SUPPORTED',
            'evidence_ids': ['SRC-001'],
        }],
        script='A PASS result tells us the test met its defined criteria. It does not automatically establish the larger scientific claim.',
        scenes=[{
            'scene_id': 'S001', 'order': 1,
            'narration': 'A PASS result tells us the test met its defined criteria.',
            'visual_prompt': 'abstract Harmony360 evidence ledger',
            'duration_seconds': 6.0,
        }],
        title='Why PASS Does Not Mean Proof',
        description='Harmony360: Building the Framework — Episode 1',
    )


def test_pipeline_reaches_storyboard(tmp_path):
    ep = build_episode(tmp_path)
    assert ep.workflow_state == 'STORYBOARDED'
    assert ep.metadata['claim_gate']['approved'] is True
    assert ep.hashes['package']


def test_human_approval_required(tmp_path):
    ep = build_episode(tmp_path)
    yt = YouTubeAdapter(memory_dir=tmp_path / 'ledger')
    try:
        yt.prepare_private_upload(ep)
        assert False, 'expected approval requirement'
    except PermissionError:
        pass

    PublicationGate(memory_dir=tmp_path / 'ledger').record_review(ep, 'human', 'APPROVE')
    payload = yt.prepare_private_upload(ep)
    assert payload['privacy_status'] == 'private'


def test_ledger_written(tmp_path):
    ep = build_episode(tmp_path)
    ledger = MediaLedger(memory_dir=tmp_path / 'har360')
    path = ledger.write_episode(ep, tmp_path / 'episode')
    assert path.exists()
    assert list((tmp_path / 'har360').glob('*.har360'))
