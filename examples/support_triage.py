"""Support-ticket triage with ONE TypeSafe call.

Setup:
    pip install typesafe-sdk
    export TYPESAFE_API_KEY=...   # from https://console.typesafe.ai/keys

Run:
    python support_triage.py
"""

from typesafe_sdk import Choice, Noul, Score, TypeSafeClient

TICKET = (
    "Hi, I've been trying to connect my Stripe account for 3 days and the "
    "integration keeps failing. I'm losing sales. Please help ASAP."
)

# Every question about the same ticket goes in ONE call: the ticket text is
# paid for once, and all questions are answered in parallel.
QUESTIONS = {
    "team": Choice(
        instructions="Which team should handle this ticket?",
        criteria={
            "billing": "Payment or subscription issues",
            "technical": "Bugs or integration problems",
            "sales": "Pricing or account questions",
            "other": "None of the above",
        },
    ),
    "urgent": Noul(instructions="The message conveys urgency or time-sensitivity."),
    "refund": Noul(instructions="The customer asks for a refund."),
    "frustration": Score(
        instructions="How frustrated does the customer appear?",
        criteria=[
            "Calm, just stating facts",
            "Frustrated but civil",
            "Very angry, strong language",
        ],
    ),
}


def main() -> None:
    with TypeSafeClient() as client:
        r = client.system_one(
            state={"ticket": TICKET},
            questions=QUESTIONS,
            model="jev-latest",
        )

    team = r.choices["team"]
    urgent = r.nouls["urgent"].noul          # probability 0..1
    refund = r.nouls["refund"].noul
    frustration = r.scores["frustration"].score

    # Plain code owns the decisions. Tune these thresholds on your own data.
    if team.confidence < 0.5:
        queue = "human-review"               # model unsure -> a person decides
    else:
        queue = team.choice

    priority = "P1" if urgent > 0.8 or frustration >= 1.5 else "P2"

    print(f"queue={queue} priority={priority} refund_flag={refund > 0.7}")
    print(f"raw: team={team.choice} ({team.confidence:.2f}) "
          f"urgent={urgent:.2f} refund={refund:.2f} frustration={frustration:.2f}")


if __name__ == "__main__":
    main()
