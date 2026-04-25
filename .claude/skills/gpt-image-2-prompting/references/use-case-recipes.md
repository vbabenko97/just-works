# GPT Image 2 Use-Case Recipes

These recipes condense common `gpt-image-2` generation and editing workflows into reusable prompting moves.

## Infographics and explainers

Best for: diagrams, process flows, timelines, labeled explainers, educational visuals.

Prompt moves:
- Define the audience and purpose.
- Describe the information hierarchy before the visual style.
- Use `quality="high"` when the asset contains dense labels or small text.
- Ask for clean spacing, readable labels, and clear grouping.

Avoid vague requests like "make an infographic about X" when factual structure matters. Provide the sequence, sections, labels, and target reading order.

## Translation or localization inside images

Best for: ads, UI screenshots, packaging, posters, infographics.

Prompt moves:
- Preserve layout, typography style, spacing, hierarchy, logos, icons, and imagery.
- Translate only the text.
- Require no extra words and no unrelated edits.
- Use edit mode with the original image as input.

Skeleton:

```text
Translate the text in the input image to [language]. Do not change any other aspect of the image. Preserve typography style, placement, spacing, hierarchy, icons, logos, colors, and imagery. Use accurate, natural [language] with no extra words.
```

## Photorealism

Best for: scenes that must feel like real photos.

Prompt moves:
- Use the word "photorealistic" directly.
- Prompt as if a real photo is being captured.
- Include real textures and imperfections: pores, fabric wear, surface scratches, dust, uneven light.
- Avoid over-polished language unless the user wants studio work.

## Logos and brand marks

Best for: early identity exploration and original marks.

Prompt moves:
- Specify brand personality and use case.
- Favor a simple silhouette and scalable design.
- Use flat/vector-like language.
- Ask for balanced negative space.
- Exclude trademarks, watermarks, gradients, and unnecessary detail.
- Use `n` to generate multiple options.

Important: ask for original, non-infringing designs. Do not imitate a living artist, existing logo, or trademarked identity.

## Ads and campaign visuals

Best for: campaign exploration, social ads, posters, hero visuals.

Prompt moves:
- Write like a creative brief.
- Include brand, audience, cultural context, concept, composition, and exact copy.
- Quote required text verbatim.
- Ask for clean, legible typography if text is in the image.
- Add constraints for no extra text, logos, or watermarks unless provided.

## UI mockups and deck-style graphics

Best for: app screens, landing-page concepts, pitch-deck slides.

Prompt moves:
- Define the interface or slide purpose.
- Specify layout, hierarchy, typography style, and components.
- Use realistic placeholder data only when acceptable.
- Ask for crisp spacing and professional visual language.
- Avoid decorative clutter unless requested.

## Style transfer

Best for: using a reference image's visual language while changing the subject.

Prompt moves:
- Identify style cues to preserve: palette, texture, brushwork, line weight, grain, lighting.
- Identify subject/content to change.
- Add hard constraints: background, framing, no extra elements.

Skeleton:

```text
Use the visual style of the input image, including [style cues], to create [new subject/scene]. Preserve the style, not the original subject. Keep [background/framing constraints]. Do not add extra elements, text, logos, or watermarks.
```

## Sketch-to-render

Best for: rough drawings, wireframes, product concepts, environment concepts.

Prompt moves:
- Preserve exact layout, proportions, and perspective.
- Add realistic materials and lighting consistent with the sketch intent.
- Avoid adding unrequested elements or text.

## Product extraction and catalog mockups

Best for: ecommerce, marketplaces, design systems.

Prompt moves:
- Preserve geometry and label legibility exactly.
- Request clean silhouette, no halos/fringing, subtle contact shadow.
- Use plain opaque background for model output when edge quality matters.
- Avoid restyling unless the user explicitly wants a redesign.

## Lighting and weather transformation

Best for: changing mood, season, time of day, weather.

Prompt moves:
- Change only environmental conditions.
- Preserve camera angle, object placement, geometry, identity, and background structure.
- Specify light direction, shadow behavior, atmosphere, precipitation, and surface changes.

## Object removal

Best for: removing small items while keeping the original image intact.

Prompt moves:
- Name the exact object to remove.
- Say "do not change anything else."
- For difficult removals, specify background reconstruction expectations.

## Person or object compositing

Best for: inserting a person/object into another scene using multiple inputs.

Prompt moves:
- Label image roles in the prompt: image 1 is the target scene, image 2 is the object/person.
- Specify exact placement.
- Match lighting, perspective, scale, color temperature, and shadows.
- Preserve the target scene except for the insertion.

## Interior design swaps

Best for: replacing furniture, decor, finishes, or materials in a room.

Prompt moves:
- Replace only the target object/material.
- Preserve camera angle, room lighting, floor shadows, surrounding objects, and style context.
- Specify realistic contact shadows and material texture.

## Multi-image character consistency

Best for: children's books, comics, mascots, storyboards.

Prompt moves:
- First establish a character anchor with appearance, outfit, proportions, personality, and style.
- For each continuation, restate core features and style.
- Use edit mode with the prior image when consistency matters.
- Add "do not redesign the character".
