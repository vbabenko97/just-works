# GPT Image 2 Prompt Templates

Use these templates as starting points. Fill only the sections that matter for the task. Delete irrelevant lines rather than padding the prompt.

## Text-to-image creative brief

```text
Create [artifact type] for [audience/use case].

Scene / subject:
[main subject, setting, action, props, context]

Composition:
[framing, viewpoint, orientation, placement, negative space, hierarchy]

Style:
[photorealistic / watercolor / vector-like / 3D render / editorial / UI / deck-style]

Quality cues:
[lighting, materials, texture, mood, color palette, realism cues]

Text, if any:
Include ONLY this text, verbatim: "[copy]"
Typography: [font style, placement, contrast, hierarchy]

Constraints:
- [no watermark / no extra text / no logos / original design only]
- [specific exclusions]
```

## Photorealistic scene

```text
Create a photorealistic image of [subject] in [environment].
The scene should feel like a real moment captured naturally, not staged.

Details:
- [skin/material/fabric/texture details]
- [natural imperfections or wear]
- [specific props or background context]

Photography:
[framing], [viewpoint], [lighting], [depth of field], [color balance].

Constraints:
- No glamorized retouching
- No overly cinematic grading unless requested
- No watermark
```

## Text-in-image asset

```text
Create [asset type] featuring [subject/brand/product].

Exact text to render, verbatim, no extra characters:
"[copy]"

Layout:
[where text appears, hierarchy, alignment, spacing]

Typography:
[bold sans-serif / serif / hand-lettered / clean UI style], high contrast, legible kerning.

Visual direction:
[scene, mood, palette, audience]

Constraints:
- Text appears once
- Preserve exact spelling and punctuation
- No extra text
- No watermark
```

Use `quality="high"` for dense text, small text, detailed infographics, or typography-heavy assets.

## Image edit prompt

```text
Edit the input image to [specific change].

Change only:
- [allowed change 1]
- [allowed change 2]

Preserve exactly:
- [identity / face / body / pose]
- [camera angle / framing / perspective]
- [background / lighting / shadows]
- [object geometry / product label / original text]

Integration requirements:
[match lighting, shadows, color temperature, scale, material behavior, perspective]

Constraints:
- Do not change anything else
- Do not add accessories, logos, watermarks, or extra text
```

## Product mockup / extraction

```text
Extract the product from the input image and place it on a plain white opaque background.

Output:
- centered product
- crisp silhouette
- no halos or fringing
- realistic contact shadow

Preserve:
- product geometry
- label legibility
- packaging colors
- printed text exactly

Constraints:
- Do not restyle the product
- Do not alter label text
- No extra elements
```

## Virtual try-on

```text
Edit the image to dress the person using the provided clothing image(s).

Preserve the person exactly:
- face and facial features
- skin tone
- body shape and proportions
- pose
- expression
- hairstyle
- identity

Replace only the clothing. Fit the garments naturally to the existing pose and body geometry with realistic fabric drape, folds, occlusion, and shadows.

Match the original photo's lighting, color temperature, camera angle, and image quality.

Constraints:
- Do not change the background
- Do not add accessories
- Do not add text, logos, or watermarks
```

## Character consistency continuation

```text
Continue the story using the same character from the input image.

Scene:
[new scene/action]

Character consistency:
- same facial features and proportions
- same outfit and color palette
- same personality and visual tone
- same age and body shape

Style:
[same illustration or visual style], [lighting], [environment], [mood]

Constraints:
- Do not redesign the character
- No text unless requested
- No watermark
```
