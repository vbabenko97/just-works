---
name: gpt-image-2-prompting
description: create and refine prompts for openai gpt-image-2 image generation and image editing workflows. use when the user asks for image prompts, prompt rewrites, production creative briefs, edit prompts, style transfer, virtual try-on, product mockups, infographics, text-in-image assets, logo or ad concepts, character consistency, or size and quality recommendations for gpt-image-2.
---

# GPT Image 2 Prompting

## Overview

Use this skill to turn a user's visual goal into a production-ready `gpt-image-2` prompt and, when helpful, API parameter recommendations. Prefer crisp creative briefs, explicit invariants, and small iterative refinements over bloated prompts that try to solve art direction, world peace, and human indecision in one paragraph.

Primary source: OpenAI Cookbook, "GPT Image Generation Models Prompting Guide" for `gpt-image-2`.

## Core behavior

1. Identify whether the user wants:
   - a text-to-image generation prompt
   - an image edit prompt
   - a prompt critique or rewrite
   - a reusable template
   - model/quality/size parameter advice
   - code for the Images API
2. Ask for missing details only when they are required. Otherwise, make sensible assumptions and state them briefly.
3. Separate what should change from what must remain fixed, especially for edits.
4. Make the output directly usable. Do not bury the prompt under generic theory.
5. If the user asks to generate or edit an image now, use the available image generation/editing tool after constructing the prompt. If they ask only for a prompt, do not generate an image.
6. Do not claim pixel-perfect, typography-perfect, identity-perfect, or policy-exempt output. Give practical controls and iteration guidance.

## Default output formats

When the user asks for a prompt, return:

```markdown
**Prompt**
[ready-to-use prompt]

**Recommended parameters**
- model: `gpt-image-2`
- size: `[resolution]`
- quality: `[low|medium|high]`
- mode: `[generate|edit]`

**Why this should work**
[2-4 concise bullets tied to the user's goal]
```

When the user asks for an edit prompt, return:

```markdown
**Edit prompt**
[ready-to-use prompt]

**Keep unchanged**
- [identity/composition/background/object/text/etc.]

**Allowed changes**
- [specific changes]

**Recommended parameters**
- model: `gpt-image-2`
- size: `[resolution]`
- quality: `[low|medium|high]`
```

When the user asks for API code, include a minimal Python snippet using `client.images.generate(...)` or `client.images.edit(...)`, plus a small helper for decoding `b64_json` only if useful.

## Prompt construction checklist

Use this order for most prompts:

1. Goal and artifact type: ad, UI mock, infographic, poster, catalog image, storyboard, logo, product photo, illustration, etc.
2. Subject and scene: who/what is visible, environment, action, era, props, context.
3. Composition: framing, viewpoint, placement, negative space, hierarchy, orientation.
4. Visual style: photorealistic, watercolor, vector-like, 3D render, editorial photo, deck-style graphic, etc.
5. Material and quality cues: lighting, texture, print quality, fabric behavior, natural imperfections, lens feel, color palette.
6. Text requirements: exact copy in quotes, placement, font style, contrast, legibility, and whether text must appear once.
7. Constraints: no watermark, no extra text, no logos, do not restyle product, preserve identity, keep background unchanged, etc.

For complex prompts, use short labeled sections rather than one dense paragraph. For production prompts, make the template skimmable and maintainable.

## Parameters and model guidance

Use `gpt-image-2` as the default for new high-quality generation and editing workflows.

Quality defaults:
- `low`: fast drafts, high-volume variants, exploration, previews.
- `medium`: general-purpose production drafts and most edits.
- `high`: dense text, detailed infographics, close-up portraits, identity-sensitive edits, high-resolution output, or when first-pass quality matters more than latency.

Size guidance:
- Square default: `1024x1024`.
- Portrait default: `1024x1536`.
- Landscape default: `1536x1024`.
- Widescreen deck/social default: `1536x864` or `2560x1440` when a larger output is justified.
- Treat outputs above `2560x1440` as more variable and experimental.

For exact `gpt-image-2` custom size validation, use `scripts/validate_gpt_image_2_size.py`.

## Generation workflows

For text-to-image generation, focus on creative direction and constraints. Good generation prompts are specific about the intended artifact and audience, not just the scene.

Use generation for:
- infographics and explainers
- photorealistic scenes
- logos and brand concepts
- ads and campaign visuals
- UI mockups and deck-style graphics
- merch, packaging, and product-style concepts
- character anchors for multi-image workflows

Load `references/use-case-recipes.md` for task-specific recipes and prompt skeletons.

## Editing workflows

For edits, explicitly lock invariants. Most edit failures come from vague prompts that let the model reinterpret the whole image, because apparently "change one thing" was too optimistic for the species.

Use edit prompts for:
- style transfer
- translation/localization inside images
- virtual try-on
- sketch-to-render
- product extraction/mockups
- text-in-image marketing creative
- lighting/weather transformation
- object removal
- person/object compositing
- interior design swaps
- character consistency continuation

Always specify:
- what source image(s) provide
- what to change
- what to preserve
- how to match lighting, perspective, scale, shadows, or typography
- what not to add

For identity-sensitive or composition-sensitive edits, keep the language firm and repetitive about invariants.

## Iteration rules

Prefer small follow-up changes over prompt pileups:
- "make lighting warmer"
- "restore the original background"
- "remove the extra object"
- "increase text contrast"
- "keep the face identical"

When revising a prompt after a bad output:
1. Diagnose the failure type: composition, text, style drift, identity drift, object addition, realism, brand mismatch, or parameter mismatch.
2. Add one or two targeted constraints.
3. Preserve all critical invariants again.
4. Avoid rewriting the entire prompt unless the original structure is fundamentally wrong.

## References

Load these only when relevant:
- `references/api-parameters.md`: model, quality, size, and code notes.
- `references/prompt-templates.md`: reusable prompt templates.
- `references/use-case-recipes.md`: recipes for common generation and editing workflows.
