from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional
import json
import re
import subprocess
import tempfile

from .core.harmony360_core import Harmony360
from .models import (
    ClaimRecord,
    EpisodePackage,
    PublicationReceipt,
    ReviewRecord,
    SceneRecord,
    SourceArtifact,
    utc_now,
)


class MediaAgent(Harmony360):
    """Shared base for every Harmony360-owned media agent.

    Mandate: every executable media class directly inherits the retained
    Harmony360 core class. No second media core is introduced.
    """

    agent_name = 'MediaAgent'

    def __init__(self, memory_dir: str | Path = './har360_output'):
        super().__init__(memory_dir=memory_dir)

    def lineage_event(self, action: str, payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        payload = payload or {}
        return {
            'agent': self.agent_name,
            'action': action,
            'at': utc_now(),
            'core_eta': self.eta,
            'payload': payload,
        }


class ResearchAgent(MediaAgent):
    agent_name = 'ResearchAgent'

    def resolve_sources(self, episode: EpisodePackage, sources: Iterable[Dict[str, Any]]) -> EpisodePackage:
        episode.sources = [SourceArtifact(**s) if not isinstance(s, SourceArtifact) else s for s in sources]
        episode.workflow_state = 'SOURCE_RESOLVED'
        episode.lineage.append(self.lineage_event('resolve_sources', {'count': len(episode.sources)}))
        return episode


class EvidenceAgent(MediaAgent):
    agent_name = 'EvidenceAgent'
    allowed_classes = {
        'established', 'implemented', 'observed', 'reported', 'experimental',
        'hypothesis', 'inferred', 'symbolic', 'unknown'
    }

    def classify_claims(self, episode: EpisodePackage, claims: Iterable[Dict[str, Any]]) -> EpisodePackage:
        normalized: List[ClaimRecord] = []
        for idx, raw in enumerate(claims, start=1):
            item = raw if isinstance(raw, ClaimRecord) else ClaimRecord(**raw)
            item.claim_class = item.claim_class.lower().strip()
            if item.claim_class not in self.allowed_classes:
                item.claim_class = 'unknown'
            if not item.claim_id:
                item.claim_id = f'{episode.episode_id}-CLAIM-{idx:03d}'
            normalized.append(item)
        episode.claims = normalized
        episode.workflow_state = 'EVIDENCE_CLASSIFIED'
        episode.lineage.append(self.lineage_event('classify_claims', {'count': len(normalized)}))
        return episode


class ScriptAgent(MediaAgent):
    agent_name = 'ScriptAgent'

    def draft_script(self, episode: EpisodePackage, script: str) -> EpisodePackage:
        episode.script = script.strip()
        episode.workflow_state = 'SCRIPT_DRAFTED'
        episode.lineage.append(self.lineage_event('draft_script', {'characters': len(episode.script)}))
        return episode


class ClaimGateAgent(MediaAgent):
    agent_name = 'ClaimGateAgent'
    high_risk_terms = {
        'proved': 'proof',
        'proven': 'proof',
        'discovered': 'discovery',
        'established': 'establishment',
        'confirms': 'confirmation',
        'demonstrates': 'demonstration',
        'causes': 'causation',
    }

    def validate_claims(self, episode: EpisodePackage) -> Dict[str, Any]:
        lower = episode.script.lower()
        flagged_terms = [term for term in self.high_risk_terms if re.search(rf'\b{re.escape(term)}\b', lower)]
        weak_claims = [c.claim_id for c in episode.claims if c.claim_class in {'experimental', 'hypothesis', 'inferred', 'symbolic', 'unknown'}]
        approved = not flagged_terms or not weak_claims
        result = {
            'approved': approved,
            'flagged_terms': flagged_terms,
            'weak_claim_ids': weak_claims,
            'rule': 'high-risk certainty language requires strong source support',
        }
        episode.metadata['claim_gate'] = result
        episode.workflow_state = 'CLAIMS_VALIDATED' if approved else 'CLAIM_REVIEW_REQUIRED'
        episode.lineage.append(self.lineage_event('validate_claims', result))
        return result


class StoryboardAgent(MediaAgent):
    agent_name = 'StoryboardAgent'

    def build_storyboard(self, episode: EpisodePackage, scenes: Iterable[Dict[str, Any]]) -> EpisodePackage:
        episode.scenes = [SceneRecord(**s) if not isinstance(s, SceneRecord) else s for s in scenes]
        episode.workflow_state = 'STORYBOARDED'
        episode.lineage.append(self.lineage_event('build_storyboard', {'count': len(episode.scenes)}))
        return episode


class VisualAgent(MediaAgent):
    agent_name = 'VisualAgent'

    def register_asset(self, episode: EpisodePackage, scene_id: str, asset_path: str, evidence_visual: bool = False) -> EpisodePackage:
        for scene in episode.scenes:
            if scene.scene_id == scene_id:
                scene.asset_path = asset_path
                scene.evidence_visual = bool(evidence_visual)
                episode.lineage.append(self.lineage_event('register_visual_asset', {
                    'scene_id': scene_id,
                    'asset_path': asset_path,
                    'evidence_visual': bool(evidence_visual),
                }))
                break
        return episode


class NarrationAgent(MediaAgent):
    agent_name = 'NarrationAgent'

    def register_narration(self, episode: EpisodePackage, audio_path: str, voice: str = 'unspecified') -> EpisodePackage:
        episode.metadata['narration'] = {'path': audio_path, 'voice': voice}
        episode.lineage.append(self.lineage_event('register_narration', episode.metadata['narration']))
        return episode


class AudioAgent(MediaAgent):
    agent_name = 'AudioAgent'

    def register_music(self, episode: EpisodePackage, music_path: str, gain_db: float = -18.0) -> EpisodePackage:
        episode.metadata['music'] = {'path': music_path, 'gain_db': gain_db}
        episode.lineage.append(self.lineage_event('register_music', episode.metadata['music']))
        return episode


class CaptionAgent(MediaAgent):
    agent_name = 'CaptionAgent'

    def write_srt(self, episode: EpisodePackage, output_path: str | Path) -> Path:
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        lines = []
        cursor = 0.0
        for idx, scene in enumerate(episode.scenes, start=1):
            start = cursor
            end = cursor + scene.duration_seconds
            cursor = end
            lines.extend([
                str(idx),
                f'{self._srt_time(start)} --> {self._srt_time(end)}',
                scene.narration.strip(),
                '',
            ])
        output_path.write_text('\n'.join(lines), encoding='utf-8')
        episode.metadata['captions'] = {'srt': str(output_path), 'style': 'sleek'}
        episode.lineage.append(self.lineage_event('write_srt', {'path': str(output_path)}))
        return output_path

    @staticmethod
    def _srt_time(seconds: float) -> str:
        ms = int(round(seconds * 1000))
        h, ms = divmod(ms, 3_600_000)
        m, ms = divmod(ms, 60_000)
        s, ms = divmod(ms, 1000)
        return f'{h:02d}:{m:02d}:{s:02d},{ms:03d}'


class RenderAgent(MediaAgent):
    agent_name = 'RenderAgent'

    def render_from_manifest(self, episode: EpisodePackage, output_path: str | Path, ffmpeg_bin: str = 'ffmpeg') -> Path:
        """Render pre-existing scene images into a vertical MP4.

        v0.1 intentionally requires local scene assets. It does not fabricate
        documentary evidence or auto-call image-generation services.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        missing = [s.scene_id for s in episode.scenes if not s.asset_path or not Path(s.asset_path).exists()]
        if missing:
            raise FileNotFoundError(f'Missing visual assets for scenes: {missing}')

        with tempfile.TemporaryDirectory() as td:
            concat = Path(td) / 'concat.txt'
            lines: List[str] = []
            for scene in episode.scenes:
                safe_path = str(Path(scene.asset_path).resolve()).replace("'", "'\\''")
                lines.append(f"file '{safe_path}'")
                lines.append(f'duration {scene.duration_seconds:.3f}')
            if episode.scenes:
                safe_path = str(Path(episode.scenes[-1].asset_path).resolve()).replace("'", "'\\''")
                lines.append(f"file '{safe_path}'")
            concat.write_text('\n'.join(lines), encoding='utf-8')

            cmd = [
                ffmpeg_bin, '-y', '-f', 'concat', '-safe', '0', '-i', str(concat),
                '-vf', 'scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2,format=yuv420p',
                '-r', '30', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', str(output_path)
            ]
            subprocess.run(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        episode.metadata['render'] = {'path': str(output_path), 'format': 'mp4', 'size': '1080x1920'}
        episode.workflow_state = 'RENDERED'
        episode.lineage.append(self.lineage_event('render_video', episode.metadata['render']))
        return output_path


class MetadataAgent(MediaAgent):
    agent_name = 'MetadataAgent'

    def generate_metadata(self, episode: EpisodePackage, title: str, description: str, tags: Optional[List[str]] = None) -> EpisodePackage:
        episode.metadata['youtube'] = {
            'title': title,
            'description': description,
            'tags': tags or ['Harmony360'],
            'privacy_status': 'private',
        }
        episode.lineage.append(self.lineage_event('generate_metadata', {'title': title}))
        return episode


class PublicationGate(MediaAgent):
    agent_name = 'PublicationGate'
    allowed_decisions = {'APPROVE', 'REJECT', 'HOLD', 'REGENERATE_SCRIPT', 'REGENERATE_VISUALS', 'RENDER_AGAIN'}

    def record_review(self, episode: EpisodePackage, reviewer: str, decision: str, notes: str = '') -> EpisodePackage:
        decision = decision.upper().strip()
        if decision not in self.allowed_decisions:
            raise ValueError(f'Unsupported review decision: {decision}')
        episode.review = ReviewRecord(reviewer=reviewer, decision=decision, notes=notes)
        episode.workflow_state = 'HUMAN_APPROVED' if decision == 'APPROVE' else decision
        episode.lineage.append(self.lineage_event('human_review', asdict(episode.review)))
        return episode

    def assert_upload_allowed(self, episode: EpisodePackage) -> None:
        if not episode.review or episode.review.decision != 'APPROVE':
            raise PermissionError('Human approval is required before upload.')
        gate = episode.metadata.get('claim_gate', {})
        if gate and not gate.get('approved', False):
            raise PermissionError('Claim gate has not approved the script.')


class YouTubeAdapter(MediaAgent):
    agent_name = 'YouTubeAdapter'

    def prepare_private_upload(self, episode: EpisodePackage) -> Dict[str, Any]:
        PublicationGate(memory_dir=self.memory.output_dir).assert_upload_allowed(episode)
        meta = episode.metadata.get('youtube', {})
        if meta.get('privacy_status', 'private') != 'private':
            raise PermissionError('v0.1 allows private upload preparation only.')
        payload = {
            'episode_id': episode.episode_id,
            'video_path': episode.metadata.get('render', {}).get('path'),
            'title': meta.get('title'),
            'description': meta.get('description'),
            'tags': meta.get('tags', []),
            'privacy_status': 'private',
        }
        episode.workflow_state = 'UPLOAD_READY'
        episode.lineage.append(self.lineage_event('prepare_private_upload', {'title': payload['title']}))
        return payload

    def record_upload_receipt(self, episode: EpisodePackage, video_id: str, url: str) -> EpisodePackage:
        episode.publication = PublicationReceipt(
            provider='youtube', external_id=video_id, url=url,
            privacy_state='private', published_at=utc_now(), status='UPLOADED'
        )
        episode.workflow_state = 'UPLOADED'
        episode.lineage.append(self.lineage_event('record_upload_receipt', {'video_id': video_id}))
        return episode


class MediaLedger(MediaAgent):
    agent_name = 'MediaLedger'

    def write_episode(self, episode: EpisodePackage, output_dir: str | Path) -> Path:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        episode.refresh_hashes()
        payload = episode.to_dict()
        json_path = output_dir / f'{episode.episode_id}.json'
        json_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding='utf-8')
        # Core-native export creates a governed .har360 receipt through Harmony360.
        self.export_har360(payload, name=episode.episode_id, tags=['media', 'youtube', episode.lifecycle.lower()])
        episode.lineage.append(self.lineage_event('write_episode_ledger', {'json_path': str(json_path)}))
        return json_path
