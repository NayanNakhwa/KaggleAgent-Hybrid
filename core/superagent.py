"""Superagent: the router and reviewer that coordinates the workers.

Graph flow:

    plan -> (fan out: one worker per subtask, via LangGraph Send) -> evaluate
         -> if some results fail judging and rounds remain: fan out again for those subtasks
         -> otherwise: synthesize -> END

Workers are spawned dynamically, one per subtask, and run in parallel within a round.
"""

from __future__ import annotations

import operator
from collections.abc import Iterator
from typing import Annotated, Any, TypedDict

from langchain_core.messages import HumanMessage, SystemMessage
from langgraph.graph import END, START, StateGraph
from langgraph.types import Send

from core.config import Settings, get_settings
from core.llm import LLMClient
from core.mcp_loader import SkillRegistry
from core.workers import ROLE_SKILLS, extract_json, run_worker

PLANNER_PROMPT = """ROLE: PLANNER
You are the superagent. Split the user's request into at most {max} independent subtasks.
Each subtask goes to one worker with role coder, executor, or researcher.
Reply with ONLY this JSON:
{"subtasks": [{"role": "coder|executor|researcher", "task": "<specific instruction>"}]}
"""

JUDGE_PROMPT = """ROLE: JUDGE
Decide whether the worker output fully completes the task.
Reply with ONLY this JSON: {"ok": true|false, "feedback": "<what to fix, empty when ok>"}
"""

SYNTH_PROMPT = """ROLE: SYNTHESIZER
Combine the subtask results into one clear answer for the user. Use markdown.
Do not mention internal agents or subtask bookkeeping. If a subtask is marked unresolved,
say which part is missing.
"""


class AgentState(TypedDict, total=False):
    request: str
    model: str
    round: int
    pending: list[dict[str, Any]]
    results: Annotated[list[dict[str, Any]], operator.add]
    accepted: Annotated[list[dict[str, Any]], operator.add]
    answer: str
    events: Annotated[list[dict[str, Any]], operator.add]


def _clean_subtasks(raw: Any, limit: int) -> list[dict[str, str]]:
    """Keep only well-formed subtasks with a known role."""
    cleaned: list[dict[str, str]] = []
    if not isinstance(raw, list):
        return cleaned
    for item in raw:
        if not isinstance(item, dict):
            continue
        role = str(item.get("role", "")).strip().lower()
        task = str(item.get("task", "")).strip()
        if role in ROLE_SKILLS and task:
            cleaned.append({"role": role, "task": task})
    return cleaned[:limit]


def _judge(llm: LLMClient, model: str, result: dict[str, Any]) -> tuple[bool, str]:
    """Return (accepted, feedback) for one worker result."""
    if not result["ok"]:
        return False, "The worker did not finish within its step budget. Use fewer, simpler steps."
    reply = llm.complete(
        [
            SystemMessage(JUDGE_PROMPT),
            HumanMessage(f"Task:\n{result['task']}\n\nOutput:\n{result['output']}"),
        ],
        model,
    )
    verdict = extract_json(reply, ("ok",))
    if verdict is None:
        return bool(result["ok"]), ""  # unparseable judge reply: trust the worker's own status
    return bool(verdict.get("ok")), str(verdict.get("feedback", ""))


def _plan_node(llm: LLMClient, settings: Settings):
    def plan(state: AgentState) -> dict[str, Any]:
        prompt = PLANNER_PROMPT.replace("{max}", str(settings.max_subtasks))
        reply = llm.complete([SystemMessage(prompt), HumanMessage(state["request"])], state["model"])
        subtasks = _clean_subtasks(
            (extract_json(reply, ("subtasks",)) or {}).get("subtasks"), settings.max_subtasks
        )
        if not subtasks:  # planner failed: fall back to one coder doing the whole request
            subtasks = [{"role": "coder", "task": state["request"]}]
        return {"round": 1, "pending": subtasks, "events": [{"type": "plan", "subtasks": subtasks}]}

    return plan


def _fan_out(state: AgentState) -> list[Send]:
    """Spawn one worker per pending subtask. Each Send carries its own payload."""
    return [
        Send(
            "worker",
            {
                "id": f"r{state['round']}-{i}",
                "round": state["round"],
                "role": item["role"],
                "task": item["task"],
                "model": state["model"],
            },
        )
        for i, item in enumerate(state["pending"])
    ]


def _worker_node(llm: LLMClient, registry: SkillRegistry, settings: Settings):
    def worker(payload: dict[str, Any]) -> dict[str, Any]:
        result = run_worker(
            role=payload["role"],
            task=payload["task"],
            llm=llm,
            model=payload["model"],
            registry=registry,
            max_steps=settings.max_worker_steps,
        )
        record = {
            "id": payload["id"],
            "round": payload["round"],
            "role": payload["role"],
            "task": payload["task"],
            **result.to_dict(),
        }
        return {
            "results": [record],
            "events": [{"type": "worker", "id": payload["id"], "role": payload["role"], "ok": result.ok}],
        }

    return worker


def _evaluate_node(llm: LLMClient, settings: Settings):
    """Reflection step: judge this round's results and decide whether to retry."""

    def evaluate(state: AgentState) -> dict[str, Any]:
        model = state["model"]
        current = [r for r in state.get("results", []) if r["round"] == state["round"]]
        accepted: list[dict[str, Any]] = []
        failed: list[tuple[dict[str, Any], str]] = []
        for result in current:
            ok, feedback = _judge(llm, model, result)
            if ok:
                accepted.append({**result, "status": "accepted"})
            else:
                failed.append((result, feedback))

        events = [
            {"type": "judge", "id": r["id"], "accepted": r not in [f[0] for f in failed]} for r in current
        ]

        if failed and state["round"] < settings.max_rounds:
            retry = [
                {
                    "role": r["role"],
                    "task": (
                        f"{r['task']}\n\nReviewer feedback on the previous attempt: {feedback}\n"
                        f"Previous output (first 1500 chars):\n{r['output'][:1500]}"
                    ),
                }
                for r, feedback in failed
            ]
            events.append({"type": "retry", "count": len(retry), "round": state["round"] + 1})
            return {"accepted": accepted, "pending": retry, "round": state["round"] + 1, "events": events}

        # Out of rounds: keep failed work marked "unresolved" so the answer can disclose it.
        unresolved = [{**r, "status": "unresolved", "feedback": fb} for r, fb in failed]
        return {"accepted": accepted + unresolved, "pending": [], "events": events}

    return evaluate


def _route_after_evaluate(state: AgentState):
    return _fan_out(state) if state.get("pending") else "synthesize"


def _synthesize_node(llm: LLMClient):
    def synthesize(state: AgentState) -> dict[str, Any]:
        blocks = []
        for item in state.get("accepted", []):
            blocks.append(
                f"### {item['role']} subtask ({item['status']})\n"
                f"Task: {item['task']}\nOutput:\n{item['output']}"
            )
        prompt = f"User request:\n{state['request']}\n\nSubtask results:\n\n" + "\n\n".join(blocks)
        answer = llm.complete([SystemMessage(SYNTH_PROMPT), HumanMessage(prompt)], state["model"]).strip()
        return {"answer": answer, "events": [{"type": "answer", "text": answer}]}

    return synthesize


def build_graph(llm: LLMClient, registry: SkillRegistry, settings: Settings | None = None):
    """Compile the superagent graph. The LLM and skill registry are injected for testability."""
    settings = settings or get_settings()
    graph = StateGraph(AgentState)
    graph.add_node("plan", _plan_node(llm, settings))
    graph.add_node("worker", _worker_node(llm, registry, settings))
    graph.add_node("evaluate", _evaluate_node(llm, settings))
    graph.add_node("synthesize", _synthesize_node(llm))
    graph.add_edge(START, "plan")
    graph.add_conditional_edges("plan", _fan_out, ["worker"])
    graph.add_edge("worker", "evaluate")
    graph.add_conditional_edges("evaluate", _route_after_evaluate, ["worker", "synthesize"])
    graph.add_edge("synthesize", END)
    return graph.compile()


def run_request(graph, request: str, model: str | None = None) -> dict[str, Any]:
    """Run to completion and return the final state."""
    inputs = {"request": request, "model": model or get_settings().default_model}
    return graph.invoke(inputs, config={"recursion_limit": 50})


def stream_events(graph, request: str, model: str | None = None) -> Iterator[dict[str, Any]]:
    """Yield progress events (plan, worker, judge, retry, answer) as each node finishes."""
    inputs = {"request": request, "model": model or get_settings().default_model}
    for update in graph.stream(inputs, stream_mode="updates", config={"recursion_limit": 50}):
        for delta in update.values():
            for event in (delta or {}).get("events", []):
                yield event
