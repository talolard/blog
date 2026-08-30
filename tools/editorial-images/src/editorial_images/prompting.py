"""Versioned prompt assembly keeps paid requests reproducible and reviewable."""

from __future__ import annotations

from .hashing import text_sha256
from .models import PostSource, Role, ROLE_SPECS
from .scene import ScenePlan

PROMPT_VERSION = "editorial-planned-v2"
MAX_PROMPT_CHARACTERS = 31_900
COMMON_DIRECTION = """Create a dramatic authored editorial photograph for a humorous, technically sophisticated personal essay.
Stage a tactile handmade physical metaphor inside a miniature practical world caught at the instant of a harmless absurd incident. Treat the ridiculous situation with the precision and seriousness of premium product photography; the humor may be deadpan, playful, warm, or chaotic as directed by the scene plan.
Use a cool-gray studio foundation, cobalt and mint accents, at most one restrained warm accent, high tonal separation, generous negative space, and minimal small detail. Do not use cream flashcard paper, ornate borders, or a children's-card look.
Both attached identity photographs show Tal Perry. Preserve Tal's recognizable face and dark curly hair while giving him scene-appropriate clothing, pose, and expression. In me2.jpeg, Tal is the adult standing behind the child; the child is not an identity reference and must not be reproduced unless the scene explicitly requires a child.
Do not include embedded text, letters, numbers, UI, source-code screenshots, logos, trademarks, watermarks, captions, frames, or factual infographic treatment. Do not imitate a living artist. Existing diagrams and screenshots are semantic references only; include subtle authentic physical details when useful, never their layout.
Use ultra-detailed tactile materials, crisp edges, realistic shadows, bright softbox key light at 45 degrees, clean bounce fill, subtle rim light, glossy highlights, and readable depth of field. The result should resemble a professional tabletop editorial photoshoot of a handmade physical set, with whimsical prop styling and cool, controlled color grading.
Keep Tal, the metaphor, and the joke immediately legible at the intended placement size."""


def role_constraints(role: Role) -> str:
    """Describe composition changes that distinguish generation from cropping."""

    spec = ROLE_SPECS[role]
    if role is Role.HERO_DESKTOP:
        composition = "Build a panoramic 3:1 composition with the focal metaphor readable across a very wide editorial banner."
    elif role is Role.HERO_MOBILE:
        composition = "Recompose the same concept as a compact 4:3 mobile hero with the focal subject large and centered; do not crop or extend the desktop image."
    else:
        composition = "Recompose the same concept as a bold 4:3 thumbnail that stays unmistakable at 120 by 90 pixels; do not crop or extend another output."
    return f"Target role: {role.value}. Exact output: {spec.size}. {composition}"


def assemble_prompt(post: PostSource, scene: ScenePlan, role: Role) -> str:
    """Render the canonical scene while keeping requests below the image API limit."""

    references = ", ".join(path.name for path in post.reference_paths) or "none"
    scene_instruction = (
        f"Prompt version: {PROMPT_VERSION}\n\n"
        f"{COMMON_DIRECTION}\n\n"
        f"Article title: {post.title}\n"
        f"Editorial thread: {post.catalog.thread}\n"
        f"Audit mode: {post.catalog.audit_mode}\n"
        f"Desired visual outcome: {post.catalog.concept}\n"
        f"Selected humor register: {scene.humor_register}\n"
        f"Physical metaphor: {scene.metaphor}\n"
        f"Miniature setting: {scene.setting}\n"
        f"Tal's role: {scene.tal_role}\n"
        f"Frozen incident: {scene.frozen_incident}\n"
        f"Physical materials: {', '.join(scene.physical_materials)}\n"
        f"Semantic anchors: {', '.join(scene.semantic_anchors)}\n"
        f"Explicit avoid list: {', '.join(scene.avoid)}\n"
        f"Declared semantic references: {references}\n"
        "Canonical image instruction from the scene planner:\n"
        f"{scene.image_instruction}\n\n"
        f"{role_constraints(role)}\n"
    )
    complete_article = (
        "\nComplete normalized article follows:\n"
        "--- ARTICLE ---\n"
        f"{post.normalized_article}"
        "--- END ARTICLE ---\n"
    )
    if len(scene_instruction) + len(complete_article) <= MAX_PROMPT_CHARACTERS:
        return scene_instruction + complete_article
    return (
        scene_instruction
        + "\nThe scene planner already read the complete normalized article; rely on its canonical instruction and semantic anchors.\n"
    )


def prompt_hash(post: PostSource, scene: ScenePlan) -> str:
    """Hash every role prompt so prompt-code changes make a post stale."""

    joined = "\n\n".join(assemble_prompt(post, scene, role) for role in Role)
    return text_sha256(joined)
