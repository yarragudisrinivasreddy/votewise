"""API Blueprint for VoteWise.

Exposes the ``/api/ask`` endpoint that accepts a user question and
returns a structured election education response.
"""

from __future__ import annotations

import logging

from flask import Blueprint, current_app, jsonify, request

from app.constants import DEFAULT_LANGUAGE
from app.election.prompt_builder import (
    build_system_prompt,
    classify_topic,
    get_follow_up_suggestions,
)
from app.exceptions import VoteWiseError
from app.models import ConversationTurn, ElectionAnswer
from app.security import derive_session_id, sanitise_question, validate_language_code

api_bp = Blueprint("api", __name__, url_prefix="/api")
logger = logging.getLogger(__name__)


@api_bp.route("/ask", methods=["POST"])
def ask():
    """Handle an election question from a user.

    Expects a JSON body with:
      - ``question`` (str, required): The user's question.
      - ``language`` (str, optional): BCP-47 language code. Defaults to ``'en'``.

    Returns:
        A JSON response containing the structured :class:`~app.models.ElectionAnswer`.

    Status codes:
        200: Successful response.
        400: Missing or invalid JSON body.
        422: Validation error on question or language field.
        500: Upstream service failure.
    """
    payload = request.get_json(silent=True) or {}

    raw_question = payload.get("question", "")
    raw_language = payload.get("language", DEFAULT_LANGUAGE)

    try:
        question = sanitise_question(raw_question)
        language = validate_language_code(raw_language)
    except VoteWiseError:
        raise

    session_id = derive_session_id(
        ip_address=request.remote_addr or "unknown",
        user_agent=request.headers.get("User-Agent", ""),
    )

    translate_svc = current_app.config["TRANSLATE"]
    gemini_svc = current_app.config["GEMINI"]
    store = current_app.config["FIRESTORE"]

    # Detect if the question is in a non-English language; if so, translate
    # to English for processing, then back to the target language for output.
    detected_lang = translate_svc.detect_language(question)
    english_question = (
        translate_svc.translate(question, "en")
        if detected_lang != "en"
        else question
    )

    topic = classify_topic(english_question)
    system_prompt = build_system_prompt(topic, language)
    history = store.load_history(session_id)

    raw_answer = gemini_svc.generate(
        system_prompt=system_prompt,
        user_prompt=english_question,
        history=history,
    )

    # Translate answer to the requested language if it is not English.
    final_answer = (
        translate_svc.translate(raw_answer, language) if language != "en" else raw_answer
    )

    turn = ConversationTurn(
        question=question,
        answer=final_answer,
        language=language,
        topic=topic,
    )
    store.append_turn(session_id, turn)

    result = ElectionAnswer(
        answer=final_answer,
        topic=topic,
        language=language,
        suggested_questions=get_follow_up_suggestions(topic),
    )

    logger.info(
        "Question answered",
        extra={"topic": topic, "lang": language, "session": session_id},
    )
    return jsonify(result.to_dict()), 200


@api_bp.route("/languages", methods=["GET"])
def languages():
    """Return the list of supported languages.

    Returns:
        JSON array of ``{code, name}`` objects.
    """
    from app.constants import SupportedLanguage

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
    from app.constants import ElectionTopic

    return jsonify({"topics": [t.value for t in ElectionTopic]}), 200
