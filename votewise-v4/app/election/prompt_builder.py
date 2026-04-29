"""Prompt construction and topic classification for VoteWise.

Builds structured prompts that combine the system persona, domain
knowledge, conversation history context, and the user's question.
Keeps Gemini focused on the Indian election domain.
"""

from __future__ import annotations

__all__ = [
    "classify_topic",
    "build_system_prompt",
    "get_follow_up_suggestions",
]

import re
from typing import Final

from app.constants import ElectionTopic, SupportedLanguage
from app.election.knowledge_base import get_facts_for_topic, get_suggestions_for_topic

#: System persona injected at the start of every Gemini prompt.
_SYSTEM_PERSONA: Final[str] = """You are VoteWise, India's trusted election education assistant.
Your mission is to help every Indian citizen — especially first-time voters and those
in rural or semi-urban areas — understand the election process clearly and confidently.

RULES:
1. Answer ONLY questions about Indian elections, voter registration, ECI, EVMs,
   constituency structure, electoral timelines, and related civic topics.
2. If the question is unrelated to elections, politely decline and suggest an election
   topic instead.
3. Use simple, clear language appropriate for a general audience.
4. Be factually accurate — do not speculate or invent information.
5. Keep answers concise: 3-5 short paragraphs maximum.
6. Always respond in the language specified by the LANGUAGE instruction.
7. End every answer with a brief encouraging note about the importance of voting.
"""

#: Keyword clusters for lightweight topic detection.
_TOPIC_KEYWORDS: Final[dict[str, list[str]]] = {
    ElectionTopic.VOTER_REGISTRATION: [
        "register", "registration", "voter id", "epic", "enroll", "roll",
        "form 6", "form 8", "पंजीकरण", "मतदाता", "నమోదు",
    ],
    ElectionTopic.HOW_TO_VOTE: [
        "how to vote", "voting", "booth", "polling", "cast", "ballot",
        "मतदान", "ఓటు", "ink", "finger",
    ],
    ElectionTopic.ECI: [
        "election commission", "eci", "nirvachan", "chief election",
        "चुनाव आयोग", "ఎన్నికల కమిషన్",
    ],
    ElectionTopic.EVM: [
        "evm", "electronic voting", "vvpat", "machine", "tamper",
        "ईवीएम", "ఈవీఎం",
    ],
    ElectionTopic.ELECTION_TYPES: [
        "lok sabha", "rajya sabha", "vidhan", "assembly", "panchayat",
        "municipal", "parliament", "लोकसभा", "విధాన సభ",
    ],
    ElectionTopic.CONSTITUENCIES: [
        "constituency", "delimitation", "seat", "reserved", "ward",
        "निर्वाचन क्षेत्र", "నియోజకవర్గం",
    ],
    ElectionTopic.TIMELINE: [
        "schedule", "timeline", "nomination", "campaign", "mcc", "model code",
        "silence period", "तारीख", "కార్యక్రమం",
    ],
    ElectionTopic.NOTA: [
        "nota", "none of the above", "reject", "नोटा",
    ],
    ElectionTopic.RESULTS: [
        "result", "count", "counting", "winner", "declared", "परिणाम", "ఫలితాలు",
    ],
}


def classify_topic(question: str) -> str:
    """Classify a user question into the most relevant :class:`~app.constants.ElectionTopic`.

    Uses a keyword-frequency approach: the topic with the most keyword
    matches against the lowercased question wins. Falls back to
    :attr:`~app.constants.ElectionTopic.GENERAL` when no keywords match.

    Args:
        question: The sanitised user question text.

    Returns:
        An :class:`~app.constants.ElectionTopic` value string.
    """
    lower = question.lower()
    scores: dict[str, int] = {topic: 0 for topic in _TOPIC_KEYWORDS}

    for topic, keywords in _TOPIC_KEYWORDS.items():
        for kw in keywords:
            if re.search(re.escape(kw), lower):
                scores[topic] += 1

    best_topic, best_score = max(scores.items(), key=lambda kv: kv[1])
    return best_topic if best_score > 0 else ElectionTopic.GENERAL


def build_system_prompt(topic: str, language: str) -> str:
    """Construct the full system prompt for a given topic and language.

    Combines the base persona, topic-specific facts, and a language
    instruction so Gemini responds in the correct language with
    relevant domain context.

    Args:
        topic: An :class:`~app.constants.ElectionTopic` value string.
        language: BCP-47 language code for the response.

    Returns:
        A multi-line system prompt string ready for injection.
    """
    facts = get_facts_for_topic(topic)
    lang_name = SupportedLanguage.display_name(language)
    facts_block = "\n".join(f"- {fact}" for fact in facts)

    return (
        f"{_SYSTEM_PERSONA}\n"
        f"LANGUAGE: Respond in {lang_name} ({language}). "
        f"If the user wrote in {lang_name}, reply in {lang_name}.\n\n"
        f"RELEVANT FACTS FOR THIS TOPIC:\n{facts_block}"
    )


def get_follow_up_suggestions(topic: str) -> list[str]:
    """Return follow-up question suggestions for a given topic.

    Args:
        topic: An :class:`~app.constants.ElectionTopic` value string.

    Returns:
        A list of suggested question strings.
    """
    return get_suggestions_for_topic(topic)
