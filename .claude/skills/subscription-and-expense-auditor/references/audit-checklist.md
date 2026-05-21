# Subscription and Expense Audit Checklist

Use this checklist when the user provides detailed transactions or a long expense list.

## Merchant patterns to inspect

- App stores: Apple, Google, Microsoft, Adobe, Setapp, JetBrains, GitHub, Notion, Slack, Figma, Canva.
- AI/API providers: OpenAI, Anthropic, Google AI, Azure OpenAI, Cohere, Mistral, Perplexity, Replicate, Hugging Face, Together, Groq, Deepgram, ElevenLabs.
- Cloud/GPU platforms: AWS, GCP, Azure, RunPod, Lambda Labs, Paperspace, Modal, Railway, Render, Vercel, Fly.io, DigitalOcean, Cloudflare.
- Data and developer services: Pinecone, Weaviate, Qdrant Cloud, Supabase, Neon, MongoDB Atlas, Datadog, Sentry, PostHog, LangSmith, WandB.
- Security and access: VPNs, password managers, domain registrars, email hosting, certificates, identity tools.
- Learning: Coursera, Udemy, edX, O'Reilly, Packt, newsletters, paid communities, bootcamps.
- Convenience spend: delivery memberships, ride subscriptions, grocery delivery fees, premium banking packages.

## Duplicate checks

Ask whether multiple tools solve the same job:

- Two or more AI chat subscriptions.
- Multiple API accounts with idle paid credits or minimum monthly fees.
- Several clouds or GPU platforms used only occasionally.
- More than one VPN or password manager.
- Multiple note-taking, task, calendar, or productivity tools.
- Paid storage on several platforms.
- Paid courses or communities not actively used.

## Risk checks before cancellation

Do not recommend immediate cancellation when the service may host or protect:

- Production workloads, DNS, domains, email, SSL certificates, or customer-facing services.
- Backups, password vaults, authentication, monitoring, logs, or incident alerts.
- Active research data, experiment tracking, model artifacts, or reproducibility records.
- Current client work, grant deliverables, invoices, or compliance records.

For these, recommend `review` or `downgrade` unless the user confirms they are unused.
