"""Deterministic graders over one completed run directory."""

import re
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path

from investment_pipeline.shared.schemas import (
    AnalysisSetV1,
    CandidateSetV1,
    RecommendationSetV1,
    RunManifestV1,
    ThesisDimension,
)
from investment_pipeline.stage_02_analysis import load_analyses
from investment_pipeline.stage_03_recommendation import assign_recommendation
from investment_pipeline.stage_03_recommendation.recommendation import MEMO_MAX_WORDS

_CITATION = re.compile(r"\[([a-z0-9_-]+)(?: · self-reported)?\]\(<https?://[^>]+>\)", re.IGNORECASE)
_RATIONALE, _RISKS, _DECISION = "## Rationale", "## Key risks", "## What would change the decision"


@dataclass(frozen=True)
class Finding:
    grader: str
    candidate_id: str | None
    message: str


@dataclass(frozen=True)
class GradedRun:
    manifest: RunManifestV1
    candidates: CandidateSetV1 | None
    analyses: AnalysisSetV1
    recommendations: RecommendationSetV1
    memos: dict[str, str]


def load_run(run_dir: Path) -> GradedRun:
    """Reload every artifact through its contract; a failure here is itself a schema finding."""
    manifest = RunManifestV1.model_validate_json(_read(run_dir / "manifest.json"))
    candidates_path = run_dir / "01_sourcing" / "candidates.json"
    candidates = (
        CandidateSetV1.model_validate_json(_read(candidates_path))
        if candidates_path.is_file()
        else None
    )
    analyses = load_analyses(run_dir / "02_analysis" / "analyses.jsonl")
    recommendations = RecommendationSetV1.model_validate_json(
        _read(run_dir / "03_recommendation" / "recommendations.json")
    )
    memos = {
        record.candidate_id: _read(run_dir / "03_recommendation" / record.memo_path)
        for record in recommendations.recommendations
        if record.memo_path is not None
    }
    return GradedRun(manifest, candidates, analyses, recommendations, memos)


def grade_grounding(run: GradedRun) -> list[Finding]:
    """Every evidence URL is the candidate's YC profile or a source the web search returned."""
    if run.candidates is None:
        return []
    profiles = {c.candidate_id: _url(c.yc_profile_url) for c in run.candidates.candidates}
    findings: list[Finding] = []
    for analysis in run.analyses.analyses:
        allowed = {
            profiles.get(analysis.candidate_id),
            *(_url(url) for url in analysis.response.source_urls),
        }
        findings.extend(
            Finding(
                "grounding",
                analysis.candidate_id,
                f"evidence {item.evidence_id} cites an unsupported URL: {item.source_url}",
            )
            for item in analysis.evidence
            if _url(item.source_url) not in allowed
        )
    return findings


def grade_policy(run: GradedRun) -> list[Finding]:
    """Ranks follow score order and every call matches the deterministic policy."""
    ordered = sorted(run.analyses.analyses, key=lambda a: (-a.total_score, a.candidate_id))
    slots = (len(ordered) + 9) // 10
    records = {record.candidate_id: record for record in run.recommendations.recommendations}
    findings = []
    for rank, analysis in enumerate(ordered, start=1):
        record = records.get(analysis.candidate_id)
        expected = assign_recommendation(analysis, rank, slots)
        if record is None:
            message = "analysis has no recommendation record"
        elif record.rank != rank:
            message = f"rank {record.rank} but score order gives {rank}"
        elif record.recommendation is not expected:
            message = f"call is {record.recommendation.value} but policy gives {expected.value}"
        else:
            continue
        findings.append(Finding("policy", analysis.candidate_id, message))
    return findings


def grade_missing_data(run: GradedRun) -> list[Finding]:
    """Missing input stays unknown instead of becoming a score or silence."""
    if run.candidates is None:
        return []
    candidates = {c.candidate_id: c for c in run.candidates.candidates}
    findings = []
    for analysis in run.analyses.analyses:
        candidate = candidates.get(analysis.candidate_id)
        if candidate is None:
            findings.append(
                Finding("missing_data", analysis.candidate_id, "analysis has no Stage 01 candidate")
            )
            continue
        founder = next(
            score
            for score in analysis.dimension_scores
            if score.dimension is ThesisDimension.FOUNDER_EXECUTION_FIT
        )
        unsupported = not candidate.founders and not analysis.response.source_urls
        if unsupported and founder.score is not None:
            findings.append(
                Finding(
                    "missing_data",
                    analysis.candidate_id,
                    "founder score given without founder data or external evidence",
                )
            )
        if candidate.traction is None and not analysis.unknowns:
            findings.append(
                Finding(
                    "missing_data",
                    analysis.candidate_id,
                    "traction is missing but no unknowns were listed",
                )
            )
    return findings


def grade_memos(run: GradedRun) -> list[Finding]:
    """Memos carry the required sections, cite only known evidence, end in the recorded call."""
    analyses = {analysis.candidate_id: analysis for analysis in run.analyses.analyses}
    findings = []
    for record in run.recommendations.recommendations:
        candidate_id = record.candidate_id
        if candidate_id not in run.memos:
            findings.append(Finding("memos", candidate_id, "memo missing: render failed"))
            continue
        text = run.memos[candidate_id]
        lines = text.splitlines()
        sections = _sections(lines)
        analysis = analyses.get(candidate_id)
        evidence_ids = {item.evidence_id for item in analysis.evidence} if analysis else set()
        problems = []
        if lines[0] != f"# {record.candidate_name}":
            problems.append("title does not match the candidate")
        if analysis and f"**Thesis score:** {analysis.total_score}/100  " not in lines:
            problems.append("thesis score differs from the analysis")
        problems.extend(
            f"missing section {heading!r}"
            for heading in (_RATIONALE, _RISKS, _DECISION)
            if heading not in sections
        )
        for heading in (_RATIONALE, _RISKS):
            for bullet in sections.get(heading, []):
                cited = _CITATION.findall(bullet)
                if not cited:
                    problems.append(f"uncited bullet under {heading!r}")
                elif unknown := set(cited) - evidence_ids:
                    problems.append(f"bullet cites unknown evidence {sorted(unknown)}")
        questions = sections.get(_DECISION, [])
        if not 2 <= len(questions) <= 3 or not all(q.endswith("?") for q in questions):
            problems.append("decision section needs two or three questions")
        if lines[-1] != f"**Recommendation: {record.recommendation.value}**":
            problems.append("final line does not state the recorded recommendation")
        if len(text.split()) > MEMO_MAX_WORDS:
            problems.append(f"memo exceeds {MEMO_MAX_WORDS} words")
        findings.extend(Finding("memos", candidate_id, problem) for problem in problems)
    return findings


GRADERS: tuple[Callable[[GradedRun], list[Finding]], ...] = (
    grade_grounding,
    grade_policy,
    grade_missing_data,
    grade_memos,
)


def _sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {}
    current = None
    for line in lines:
        if line.startswith("## "):
            current = line
            sections[current] = []
        elif current is not None and line.startswith("- "):
            sections[current].append(line[2:])
    return sections


def _url(url: object) -> str:
    return str(url).casefold().rstrip("/")


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")
