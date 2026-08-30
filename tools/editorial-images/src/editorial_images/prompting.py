"""Versioned prompt assembly keeps paid requests reproducible and reviewable."""

from __future__ import annotations

from .hashing import text_sha256
from .models import PostSource, Role, ROLE_SPECS

PROMPT_VERSION = "editorial-v1"
COMMON_DIRECTION = """Create cool editorial art for a technically sophisticated personal essay.
Use one strong focal metaphor, high contrast, a cool gray foundation, cobalt and mint accents, restrained texture, and minimal small detail.
The result should feel like an authored magazine illustration with precision and a trace of mischief.
Do not include embedded text, letters, numbers, UI, source-code screenshots, logos, trademarks, watermarks, captions, frames, or factual infographic treatment.
Do not imitate a living artist. Existing diagrams and screenshots are semantic references only, never layout templates.
Keep the focal idea immediately legible at the intended placement size."""


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


def assemble_prompt(post: PostSource, role: Role) -> str:
    """Include the complete normalized English article without truncation."""

    references = ", ".join(path.name for path in post.reference_paths) or "none"
    return (
        f"Prompt version: {PROMPT_VERSION}\n\n"
        f"{COMMON_DIRECTION}\n\n"
        f"Article title: {post.title}\n"
        f"Editorial thread: {post.catalog.thread}\n"
        f"Audit mode: {post.catalog.audit_mode}\n"
        f"Desired visual outcome: {post.catalog.concept}\n"
        f"Declared semantic references: {references}\n"
        f"{role_constraints(role)}\n\n"
        "Complete normalized article follows:\n"
        "--- ARTICLE ---\n"
        f"{post.normalized_article}"
        "--- END ARTICLE ---\n"
    )


def prompt_hash(post: PostSource) -> str:
    """Hash every role prompt so prompt-code changes make a post stale."""

    joined = "\n\n".join(assemble_prompt(post, role) for role in Role)
    return text_sha256(joined)
