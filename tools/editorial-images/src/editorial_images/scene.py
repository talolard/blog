"""Persist one reviewed scene instruction between planning and rendering."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, ValidationError

from .hashing import text_sha256
from .models import PostSource

SCENE_FILENAME = "scene-plan.json"
PLANNER_VERSION = "tal-editorial-scene-v1"
HumorRegister = Literal["deadpan", "playful", "warm", "chaotic"]


class ScenePlan(BaseModel):
    """The canonical, ratio-independent art direction produced for one post."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    metaphor: str
    setting: str
    humor_register: HumorRegister
    tal_role: str
    frozen_incident: str
    physical_materials: tuple[str, ...]
    semantic_anchors: tuple[str, ...]
    avoid: tuple[str, ...]
    image_instruction: str


class ScenePlanRecord(BaseModel):
    """A stored scene plus enough provenance to detect changed planning inputs."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1] = 1
    status: Literal["complete"] = "complete"
    planner_version: str
    planner_input_hash: str
    planner_model: str
    planned_at: str
    response_id: str
    scene: ScenePlan


def planning_prompt(post: PostSource) -> str:
    """Capture the settled visual system and every post-specific semantic input."""

    references = ", ".join(path.name for path in post.reference_paths) or "none"
    return f"""Planner version: {PLANNER_VERSION}

Design exactly one canonical editorial photograph for this article.

Shared visual system:
- Adapt the V2 dual-scene flashcard grammar without copying its flashcard identity.
- Use a tactile handmade physical metaphor, a miniature practical set, generous negative space, and polished studio photography.
- Replace cream paper, ornate borders, and a children's palette with the website's cool-gray foundation, cobalt and mint accents, and at most one restrained warm accent.
- Choose the humor register that fits this post: deadpan, playful, warm, or chaotic. The photographic treatment remains serious even when the situation is ridiculous.
- Prefer a hybrid scene: the physical metaphor lives in a miniature world caught at the instant of a harmless absurd incident. A calm exception is allowed when the article demands it.
- Make the abstract idea physically literal using objects and materials native to the article. Avoid generic symbolic illustration and generic cute robots.
- Tal Perry must appear as a recognizable character with a scene-specific role: protagonist, operator, observer, or accidental cause. The two supplied photos show Tal. In the second photo Tal is the adult behind the child; the child is not an identity reference.
- Preserve one canonical cast, setting, prop system, and incident across desktop, mobile, and thumbnail recompositions.
- The idea and joke must survive at 120 by 90 pixels: one dominant subject, a thick simple silhouette, high tonal separation, and no more than three large supporting props.
- The scene must also work as a native 3:1 banner: arrange action laterally and do not depend on a tall central construction.
- No embedded text, letters, numbers, UI, logos, trademarks, watermarks, factual infographic layout, injury, humiliation, or gross-out imagery.
- Existing diagrams and screenshots are semantic evidence only. Borrow authentic physical details, never their layout.

Return a concrete scene, not general advice. The final image_instruction must be a self-contained 140-220 word direction suitable for an image model. It must describe Tal's action and expression, the physical metaphor, the setting, the frozen incident, material and lighting cues, color hierarchy, and the invariants that make the scene work in all three ratios. Do not mention JSON, this planning step, or the article text in image_instruction.

Article title: {post.title}
Editorial thread: {post.catalog.thread}
Existing visual goal: {post.catalog.concept}
Audit mode: {post.catalog.audit_mode}
Semantic reference files: {references}

Complete normalized article:
--- ARTICLE ---
{post.normalized_article}--- END ARTICLE ---
"""


def planner_input_hash(post: PostSource) -> str:
    """Hash prose, goals, planner rules, and both identity photographs."""

    identity = "\n".join(f"{name}:{digest}" for name, digest in post.identity_hashes)
    return text_sha256(f"{planning_prompt(post)}\n{identity}")


def new_record(post: PostSource, scene: ScenePlan, *, model: str, response_id: str) -> ScenePlanRecord:
    """Attach deterministic source provenance to a newly planned scene."""

    return ScenePlanRecord(
        planner_version=PLANNER_VERSION,
        planner_input_hash=planner_input_hash(post),
        planner_model=model,
        planned_at=datetime.now(UTC).isoformat().replace("+00:00", "Z"),
        response_id=response_id,
        scene=scene,
    )


def scene_path(post: PostSource) -> Path:
    """Return the co-located plan path for a post bundle."""

    return post.bundle / SCENE_FILENAME


def load_record(path: Path) -> ScenePlanRecord:
    """Parse a stored plan through the same strict schema used by the API."""

    return ScenePlanRecord.model_validate_json(path.read_text(encoding="utf-8"))


def current_record(post: PostSource) -> ScenePlanRecord | None:
    """Return only a valid plan built from the current article, goals, and photos."""

    path = scene_path(post)
    if not path.is_file():
        return None
    try:
        record = load_record(path)
    except (OSError, ValidationError):
        return None
    if record.planner_version != PLANNER_VERSION or record.planner_input_hash != planner_input_hash(post):
        return None
    return record


def render_record(record: ScenePlanRecord) -> str:
    """Serialize stable, human-reviewable planner output."""

    return record.model_dump_json(indent=2) + "\n"


def scene_hash(record: ScenePlanRecord) -> str:
    """Hash the exact canonical scene consumed by image-role prompts."""

    return text_sha256(record.scene.model_dump_json())
