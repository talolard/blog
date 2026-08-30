# Personal Editorial Scene Planner

## Settled direction

The editorial art system borrows the physical-comedy grammar of the Maya's Cards V2
dual-scene prompts without copying the flashcard identity.

- Keep tactile real-world materials, handmade miniature sets, generous negative
  space, crisp studio photography, and one dominant physical metaphor.
- Replace cream paper, decorative borders, and the children's palette with the
  website's cool-gray foundation, cobalt and mint accents, and at most one restrained
  warm accent.
- Choose the humor register per post: deadpan, playful, warm, or chaotic.
- Default to a hybrid scene: a physical metaphor in a miniature world, caught at the
  instant of a harmless absurd incident. Allow calmer exceptions when the article
  needs them.
- Make abstract ideas physically literal using objects and materials native to the
  article. Avoid generic symbolic illustrations and generic cute robots.
- Select one canonical scene before rendering. Do not pay for two competing concepts
  by default.
- Preserve the same cast, props, setting, and joke across desktop, mobile, and
  thumbnail recompositions.
- Tal Perry appears recognizably in every illustration as the protagonist, operator,
  observer, or accidental cause. `me1.jpeg` and `me2.jpeg` are supplied to both the
  planner and every image request. In `me2.jpeg`, the adult is the identity target;
  the child is not.

## Prompt architecture

The pipeline has a typed, persisted boundary between two models:

1. A pinned multimodal planner reads the complete English article, catalog concept,
   declared semantic references, and both Tal identity photos.
2. It emits one structured scene containing the metaphor, setting, humor register,
   Tal's role, frozen incident, physical materials, semantic anchors, avoid-list, and
   a self-contained image instruction.
3. The result is stored as co-located `scene-plan.json` with its planner version,
   input hash, model, timestamp, and response ID.
4. GPT Image 2 receives that instruction, the complete article, role constraints,
   both identity photos, and applicable semantic or desktop references.
5. Desktop renders first. Thumbnail and mobile render concurrently from the desktop
   result and both identity photographs.

A normal forced rerun reuses the stored scene. `--replan --force` is the explicit
operation that replaces the scene and all three images. Planner inputs include both
photo hashes, the complete article, the catalog concept, and the versioned planning
rules, so a changed input makes the bundle stale.

## Placement constraints

- At 120×90, use one large subject, a thick simple silhouette, high tonal separation,
  and no more than three large supporting props.
- At 3:1, arrange the metaphor and action laterally. Never depend on a tall central
  construction or merely shrink a vertical composition into empty side space.
- Tal, the metaphor, and the comic incident must remain understandable in every role.
- No embedded text, UI, logos, watermarks, factual infographic layouts, gross-out
  imagery, injury, or humiliation.
