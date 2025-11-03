import sys
import os

# This line adds the parent directory to the Python path
# so you can import from 'config' and 'agent'
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import config
from agent.tools import all_tools

# Try to use the LangChain agent if available; otherwise fall back to the
# programmatic orchestrator in `auto_apply.py` so this script remains useful
# even when LangChain/OpenAI packages are not installed.
USE_LC = True
try:
    from langchain_openai import ChatOpenAI
    from langchain.agents import initialize_agent, AgentType
except Exception:
    USE_LC = False


if USE_LC:
    # 1. Initialize the LLM
    llm = ChatOpenAI(model="gpt-4o", temperature=0)

    # 2. Initialize the Agent (OpenAI functions style)
    agent_executor = initialize_agent(
        all_tools,
        llm,
        agent=AgentType.OPENAI_FUNCTIONS,
        verbose=True,
    )


def run_with_langchain(limit: int = 2):
    user_prompt = f"Find {limit} 'Data Analyst' jobs. For each job, get its full description. After you have the description, apply to the job. Report the final status for each job."
    print("--- Starting AI Job Agent (LangChain) ---")
    result = agent_executor.invoke({
        "input": user_prompt
    })
    print("--- Agent finished ---")
    print(f"Final Output: {result.get('output')}")


def run_fallback(title: str = "Data Analyst", location: str = "remote", limit: int = 2, dry_run: bool = True):
    # Local fallback: programmatic runner
    print("LangChain not available — using programmatic auto-apply fallback.")
    try:
        from auto_apply import run_auto_apply
    except Exception as e:
        print(f"Failed to import auto_apply: {e}")
        raise

    results = run_auto_apply(title=title, location=location, limit=limit, dry_run=dry_run)
    print("Summary from fallback run:")
    for r in results:
        print(f"{r['job'].get('title')} @ {r['job'].get('company')}: {r['status']}")


if __name__ == "__main__":
    # CLI-compatible quick entrypoint
    import argparse

    parser = argparse.ArgumentParser(description="Run the AI job agent (LangChain if available, else fallback)")
    parser.add_argument("--limit", type=int, default=2)
    parser.add_argument("--title", default="Data Analyst")
    parser.add_argument("--location", default="remote")
    parser.add_argument("--no-dry-run", dest="dry_run", action="store_false", help="Disable dry-run (not recommended)")
    parser.add_argument("--dry-run", dest="dry_run", action="store_true", default=True)
    args = parser.parse_args()

    if USE_LC:
        run_with_langchain(limit=args.limit)
    else:
        run_fallback(title=args.title, location=args.location, limit=args.limit, dry_run=args.dry_run)