import json

from app.surface import observe
from app.decision_engine import decide_next_action
from app.action_executor import execute_action


def run_agent_loop(
    page,
    goal,
    max_steps=10
):

    history = []

    for step in range(max_steps):

        print(f"\n===== STEP {step + 1} =====")

        # Observe
        observation = observe(page)

        print("\nOBSERVATION\n")

        print(
            json.dumps(
                observation,
                indent=4
            )
        )

        # Decide
        decision = decide_next_action(
            goal,
            observation
        )

        print("\nDECISION\n")

        print(
            json.dumps(
                decision,
                indent=4
            )
        )

        # Act
        result = execute_action(
            page,
            decision
        )

        print("\nACTION RESULT\n")

        print(
            json.dumps(
                result,
                indent=4
            )
        )

        history.append(
            {
                "step": step + 1,
                "observation": observation,
                "decision": decision,
                "result": result
            }
        )

        # Stop condition

        if decision.get("action") == "finish":

            print(
                "\nGoal Complete"
            )

            break

    return history