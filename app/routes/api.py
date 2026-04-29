"""API Blueprint for VoteWise.

Exposes the ``/api/ask`` endpoint that accepts a user question and
returns a structured election education response.
"""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request

from app.constants import DEFAULT_LANGUAGE, ElectionTopic, SupportedLanguage
from app.election.prompt_builder import (
    build_system_prompt,
    classify_topic,
    get_follow_up_suggestions,
)
from app.models import ConversationTurn, ElectionAnswer
from app.security import derive_session_id, sanitise_question, validate_language_code

from app.middleware.rate_limit import limiter

api_bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


def _resolve_english_question(question: str, translate_svc) -> str:
    """Translate ``question`` to English if it is in another language.

    Args:
        question: The sanitised user question, possibly in a non-English language.
        translate_svc: An active :class:`~app.services.translate.CloudTranslateService`.

    Returns:
        The question in English.
    """
    detected_lang = translate_svc.detect_language(question)
    if detected_lang != "en":
        return translate_svc.translate(question, "en")
    return question


def _build_answer(english_question: str, language: str, session_id: str) -> ElectionAnswer:
    """Generate and translate an election answer for the given question.

    Orchestrates topic classification, prompt construction, Gemini generation,
    and response translation into a single cohesive answer object.

    Args:
        english_question: The user question normalised to English.
        language: BCP-47 target language for the response.
        session_id: Anonymised session identifier for conversation history.

    Returns:
        A populated :class:`~app.models.ElectionAnswer`.
    """
    translate_svc = current_app.config["TRANSLATE"]
    gemini_svc = current_app.config["GEMINI"]
    store = current_app.config["FIRESTORE"]

    topic = classify_topic(english_question)
    system_prompt = build_system_prompt(topic, language)
    history = store.load_history(session_id)

    raw_answer = gemini_svc.generate(
        system_prompt=system_prompt,
        user_prompt=english_question,
        history=history,
    )

    final_answer = (
        translate_svc.translate(raw_answer, language) if language != "en" else raw_answer
    )

    return ElectionAnswer(
        answer=final_answer,
        topic=topic,
        language=language,
        suggested_questions=get_follow_up_suggestions(topic),
    )


@api_bp.route("/ask", methods=["POST"])
@limiter.limit("30 per minute")
def ask():
    """Handle an election question from a user.

    Expects a JSON body with:
      - ``question`` (str, required): The user's question.
      - ``language`` (str, optional): BCP-47 language code. Defaults to ``'en'``.

    Returns:
        A JSON response containing the structured :class:`~app.models.ElectionAnswer`.

    Status codes:
        200: Successful response.
        422: Validation error on question or language field.
        500: Upstream service failure.
    """
    payload = request.get_json(silent=True) or {}
    question = sanitise_question(payload.get("question", ""))
    language = validate_language_code(payload.get("language", DEFAULT_LANGUAGE))

    session_id = derive_session_id(
        ip_address=request.remote_addr or "unknown",
        user_agent=request.headers.get("User-Agent", ""),
    )

    translate_svc = current_app.config["TRANSLATE"]
    english_question = _resolve_english_question(question, translate_svc)
    result = _build_answer(english_question, language, session_id)

    store = current_app.config["FIRESTORE"]
    store.append_turn(
        session_id,
        ConversationTurn(
            question=question,
            answer=result.answer,
            language=language,
            topic=result.topic,
        ),
    )

    logger.info(
        "Question answered",
        extra={"topic": result.topic, "lang": language, "session": session_id},
    )
    return jsonify(result.to_dict()), 200


@api_bp.route("/languages", methods=["GET"])
def languages():
    """Return the list of supported languages.

    Returns:
        JSON array of ``{code, name}`` objects.
    """
    langs = [
        {"code": lang, "name": SupportedLanguage.display_name(lang)}
        for lang in SupportedLanguage.values()
    ]
    return jsonify({"languages": langs}), 200


@api_bp.route("/topics", methods=["GET"])
def topics():
    """Return the list of supported election topics.

    Returns:
        JSON array of topic value strings.
    """
    return jsonify({"topics": [t.value for t in ElectionTopic]}), 200
