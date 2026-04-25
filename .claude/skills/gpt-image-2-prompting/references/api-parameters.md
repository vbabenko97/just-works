# GPT Image 2 API Parameters

Source: OpenAI Cookbook, "GPT Image Generation Models Prompting Guide" (April 21, 2026).

## Model selection

Use `gpt-image-2` as the default for new image generation and editing workflows, especially for:

- customer-facing assets
- photorealistic generation
- editing-heavy flows
- brand-sensitive creative
- text-heavy images
- identity-sensitive edits
- workflows where fewer retries are more valuable than the lowest possible cost

Use `gpt-image-1-mini` only when cost and throughput dominate and visual stakes are lower. Keep `gpt-image-1.5` or `gpt-image-1` only for validated legacy workflows during migration.

## Quality selection

`gpt-image-2` supports:

- `low`: fastest option for drafts, previews, high-volume exploration, and variant generation.
- `medium`: sensible default for general generation and editing.
- `high`: use for dense text, detailed infographics, close-up portraits, high-resolution images, brand-sensitive outputs, and identity-sensitive edits.

Rule of thumb: if review time and retries are more expensive than generation time, start with `medium` or `high`. If volume and latency dominate, start with `low`, then promote only the winners.

## Size constraints for gpt-image-2

Custom `size` values must satisfy all constraints:

- maximum edge length must be less than `3840px`
- both edges must be multiples of `16`
- long edge / short edge ratio must be no greater than `3:1`
- total pixels must not exceed `8,294,400`
- total pixels must not be less than `655,360`

Outputs above `2560x1440` can be more variable. Treat them as experimental unless the workflow has been validated.

## Common sizes

- `1024x1024`: square default.
- `1024x1536`: portrait default.
- `1536x1024`: landscape default.
- `1536x864`: 16:9 deck/social/widescreen draft.
- `2560x1440`: larger 16:9 output near the recommended reliability boundary.
- `3824x2144`: practical near-4K 16:9 size that keeps the longest edge below 3840 and both edges divisible by 16.

## Generate API pattern

```python
from openai import OpenAI

client = OpenAI()

result = client.images.generate(
    model="gpt-image-2",
    prompt=prompt,
    size="1024x1536",
    quality="medium",
)
```

Use `n` for multiple variants when the workflow benefits from exploration, such as logos or campaign directions.

## Edit API pattern

```python
from openai import OpenAI

client = OpenAI()

result = client.images.edit(
    model="gpt-image-2",
    image=[open("input.png", "rb")],
    prompt=prompt,
    size="1024x1536",
    quality="medium",
)
```

For multi-image compositing, pass multiple files in `image=[...]` and identify each image's role in the prompt, for example "image 1 is the room, image 2 is the chair to insert."

## Background handling

For product mockups where a clean background is needed, use an opaque background when appropriate and rely on downstream background removal if a transparent final asset is required. This helps preserve product edges and label integrity.

## Migration notes

When moving from `gpt-image-1.5` or `gpt-image-1`, keep prompts mostly unchanged at first. Compare output quality, latency, and retry rate on real workload samples before retuning. Retuning before measuring is how teams accidentally invent expensive superstition with YAML.
