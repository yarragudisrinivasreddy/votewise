"""Election domain knowledge base for VoteWise.

Provides structured, authoritative information about the Indian
election process used to build context-rich prompts for Gemini.
"""

from __future__ import annotations

from app.constants import ElectionTopic

#: Mapping from topic to a curated list of quick-reference facts.
TOPIC_FACTS: dict[str, list[str]] = {
    ElectionTopic.VOTER_REGISTRATION: [
        "Citizens aged 18+ who are ordinarily resident at a place are eligible to register.",
        "Register online at voters.eci.gov.in or through the Voter Helpline App.",
        "Form 6 is used for new registrations; Form 8 for corrections.",
        "EPIC (Elector's Photo Identity Card) is issued after successful registration.",
        "The electoral roll is revised annually; the qualifying date is 1 January each year.",
    ],
    ElectionTopic.HOW_TO_VOTE: [
        "Bring a valid photo ID (EPIC, Aadhaar, Passport, etc.) to the polling station.",
        "Find your booth number using voters.eci.gov.in or the Voter Helpline App.",
        "Polling hours are typically 7:00 AM to 6:00 PM.",
        "The EVM ballot unit displays candidate names and symbols with corresponding buttons.",
        "Press the button against your chosen candidate; the VVPAT slip confirms your vote.",
        "Indelible ink is applied to the left index finger after voting.",
    ],
    ElectionTopic.ECI: [
        "The Election Commission of India (ECI) is a constitutional body under Article 324.",
        "It consists of a Chief Election Commissioner and two Election Commissioners.",
        "ECI superintends, directs, and controls the preparation of electoral rolls and elections.",
        "It can impose the Model Code of Conduct (MCC) from the date of election announcement.",
        "Headquarters: Nirvachan Sadan, Ashoka Road, New Delhi.",
    ],
    ElectionTopic.EVM: [
        "EVMs consist of a Control Unit (at polling officer's table) and a Ballot Unit (for voters).",
        "VVPAT (Voter Verified Paper Audit Trail) prints a slip visible to the voter for 7 seconds.",
        "EVMs are standalone devices with no wireless or internet connectivity.",
        "Each EVM can record a maximum of 2,000 votes.",
        "EVMs run on 6V alkaline batteries and are not connected to any power supply during voting.",
    ],
    ElectionTopic.ELECTION_TYPES: [
        "Lok Sabha: 543 directly elected constituencies; 5-year term.",
        "Rajya Sabha: Upper house; 238 elected by state assemblies; 6-year staggered terms.",
        "Vidhan Sabha: State legislative assemblies; 5-year term.",
        "Panchayat elections: Village-level governance; conducted by State Election Commissions.",
        "Municipal elections: Urban local bodies; conducted by State Election Commissions.",
        "Presidential and Vice-Presidential elections are conducted by the ECI.",
    ],
    ElectionTopic.CONSTITUENCIES: [
        "India is divided into 543 Parliamentary Constituencies for Lok Sabha elections.",
        "Each state is further divided into Assembly Constituencies for Vidhan Sabha.",
        "Delimitation is carried out by the Delimitation Commission to equalise voter representation.",
        "The last delimitation was carried out in 2008 based on the 2001 census.",
        "Some seats are reserved for Scheduled Castes (SC) and Scheduled Tribes (ST).",
    ],
    ElectionTopic.TIMELINE: [
        "ECI announces the election schedule; the MCC comes into effect immediately.",
        "Notification: Official announcement published in the Official Gazette.",
        "Last date of nomination filing: Typically 7 days after notification.",
        "Scrutiny of nominations: 1 day after last date of nomination.",
        "Withdrawal of candidature: Up to 2 days after scrutiny.",
        "Campaign period: Ends 48 hours before polling (Silence Period).",
        "Polling day: Voters cast their ballots.",
        "Counting of votes: Usually held a few days after polling.",
        "Declaration of results: Same day as counting.",
    ],
    ElectionTopic.NOTA: [
        "NOTA (None of the Above) was introduced by the Supreme Court in 2013.",
        "The NOTA option appears at the bottom of the ballot/EVM.",
        "NOTA votes are counted but do not affect the outcome; the candidate with most votes still wins.",
        "NOTA is represented by a ballot paper crossed out with a black circle.",
    ],
    ElectionTopic.RESULTS: [
        "Counting is conducted at designated Counting Centres under ECI supervision.",
        "Postal ballots are counted first, followed by EVM votes.",
        "Counting agents of each candidate are present to observe.",
        "Results are declared constituency by constituency as counting completes.",
        "The winning candidate must file election expenses within 30 days.",
    ],
}

#: Suggested follow-up questions per topic, used to guide exploration.
SUGGESTED_QUESTIONS: dict[str, list[str]] = {
    ElectionTopic.VOTER_REGISTRATION: [
        "What documents do I need to register as a voter?",
        "How can I check if my name is on the electoral roll?",
        "What should I do if my address has changed?",
    ],
    ElectionTopic.HOW_TO_VOTE: [
        "What ID documents are accepted at the polling booth?",
        "How does the VVPAT confirm my vote?",
        "What happens if I make a mistake on the EVM?",
    ],
    ElectionTopic.ECI: [
        "What powers does the ECI have over political parties?",
        "How is the Chief Election Commissioner appointed?",
        "What is the Model Code of Conduct?",
    ],
    ElectionTopic.EVM: [
        "Can EVMs be tampered with?",
        "What is VVPAT and how does it work?",
        "How are EVMs tested before elections?",
    ],
    ElectionTopic.ELECTION_TYPES: [
        "What is the difference between Lok Sabha and Rajya Sabha?",
        "How are Rajya Sabha members elected?",
        "What is a by-election?",
    ],
    ElectionTopic.GENERAL: [
        "How do I register to vote?",
        "What is the election process in India?",
        "How does the EVM work?",
    ],
}


def get_facts_for_topic(topic: str) -> list[str]:
    """Return the curated fact list for a given election topic.

    Args:
        topic: An :class:`~app.constants.ElectionTopic` value string.

    Returns:
        A list of fact strings. Falls back to an empty list if the
        topic is not in :data:`TOPIC_FACTS`.
    """
    return TOPIC_FACTS.get(topic, [])


def get_suggestions_for_topic(topic: str) -> list[str]:
    """Return suggested follow-up questions for a given topic.

    Args:
        topic: An :class:`~app.constants.ElectionTopic` value string.

    Returns:
        A list of suggested question strings.
    """
    return SUGGESTED_QUESTIONS.get(topic, SUGGESTED_QUESTIONS[ElectionTopic.GENERAL])
