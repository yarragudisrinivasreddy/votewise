# VoteWise — India's Election Education Assistant

**VoteWise** is an AI-powered civic education assistant that helps every Indian citizen understand the election process — from voter registration to results counting — in 7 Indian languages.

## Chosen Vertical

**Election Process Education** — Create an assistant that helps users understand the election process, timelines, and steps in an interactive and easy-to-follow way.

## Problem Statement

Millions of Indian citizens, especially first-time voters and those in rural or semi-urban areas, lack accessible, multilingual guidance on the election process. VoteWise bridges this gap by providing instant, accurate answers in the user's preferred language.

## Approach & Logic

1. **Language detection** via Cloud Translate v3 identifies the user's input language.
2. **Topic classification** maps the question to a specific election domain (voter registration, EVMs, ECI, NOTA, etc.) using keyword analysis.
3. **Prompt construction** combines the classified topic with curated domain knowledge facts and injects them into the Gemini system prompt.
4. **Gemini generation** (via Vertex AI) produces a factual, empathetic answer.
5. **Translation** delivers the response in the user's selected language (full answer translation, not just input).
6. **Conversation history** stored in Firestore provides multi-turn context.

## Google Services Integrated

| Service | Usage |
|---------|-------|
| Vertex AI (Gemini 2.5 Flash) | Core answer generation via `vertexai.init()` |
| Cloud Translate v3 | Language detection + full response translation |
| Cloud Firestore | Persistent conversation history per session |
| Cloud Storage | Session log archival |
| Secret Manager | Secure runtime secret retrieval |

## Architecture

```
app/
├── __init__.py          # App factory (Flask)
├── config.py            # Immutable configuration dataclass
├── constants.py         # Typed enums — zero magic strings
├── exceptions.py        # Custom exception hierarchy
├── logging_config.py    # Structured JSON logging for Cloud Logging
├── security.py          # Input sanitisation & validation
├── models/              # Typed request/response dataclasses
├── services/            # Protocol-based service implementations
│   ├── interfaces.py    # Structural typing protocols (PEP 544)
│   ├── gemini.py        # Vertex AI / Gemini service
│   ├── translate.py     # Cloud Translate v3 with TTL cache
│   ├── firestore.py     # Conversation store
│   └── secret_storage.py # Secret Manager + Cloud Storage
└── election/
    ├── knowledge_base.py # Curated election domain facts
    └── prompt_builder.py # Topic classifier + prompt construction
```

## How It Works

1. User types a question in any supported language.
2. VoteWise detects the language and topic automatically.
3. Gemini generates a concise, accurate answer using domain-specific context.
4. The answer is delivered in the user's language.
5. Follow-up question chips guide further exploration.

## Supported Languages

English · हिन्दी · తెలుగు · தமிழ் · मराठी · বাংলা · ಕನ್ನಡ

## Deployment

```bash
# Set up Firestore
gcloud firestore databases create --location=asia-south1

# Deploy to Cloud Run
gcloud run deploy votewise \
  --source=. \
  --region=asia-south1 \
  --allow-unauthenticated \
  --set-env-vars=GOOGLE_CLOUD_PROJECT=YOUR_PROJECT_ID \
  --memory=512Mi \
  --timeout=120
```

## Testing

```bash
pip install pytest pytest-cov
pytest --cov=app tests/
```

## Assumptions

- Users have valid Google Cloud credentials in the deployment environment.
- Firestore must be created before first deployment: `gcloud firestore databases create --location=asia-south1`
- The Cloud Storage bucket is created automatically on first archive operation.
