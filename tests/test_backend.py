"""Backend tests: no network and no Ollama needed. The LLM is replaced with a scripted fake."""

import json
import sys
from pathlib import Path

import pytest

from core.mcp_loader import load_skills_from_dir
from core.superagent import build_graph, run_request
from core.workers import extract_json, run_worker


class ScriptedLLM:
    """Returns canned replies in order. The last reply repeats once the script runs out."""

    def __init__(self, replies):
        self.replies = list(replies)
        self.calls = 0

    def complete(self, messages, model):
        self.calls += 1
        if len(self.replies) > 1:
            return self.replies.pop(0)
        return self.replies[0]


@pytest.fixture
def workspace(tmp_path, monkeypatch):
    ws = tmp_path / "ws"
    ws.mkdir()
    skills = Path(__file__).resolve().parents[1] / "workspace" / "mcp_skills"
    monkeypatch.setenv("KAGENT_WORKSPACE", str(ws))
    monkeypatch.setenv("KAGENT_SKILLS_DIR", str(skills))
    return ws


@pytest.fixture
def registry(workspace):
    return load_skills_from_dir()


def test_default_skills_load(registry):
    expected = {"file_editor", "file_explorer", "bash_terminal", "python_repl", "linter", "web_docs"}
    assert expected <= set(registry.names())
    assert registry.load_errors == {}


def test_template_is_ignored(registry):
    assert "example_skill" not in registry.names()


def test_bad_skill_is_skipped(tmp_path):
    d = tmp_path / "skills"
    d.mkdir()
    (d / "broken.py").write_text("SKILL_NAME = 'Bad Name'\n")
    (d / "good.py").write_text(
        'SKILL_NAME = "good_one"\nDESCRIPTION = "ok"\n'
        'PARAMETERS = {"type": "object", "properties": {}}\n'
        "def run():\n    return 'hi'\n"
    )
    reg = load_skills_from_dir(d)
    assert reg.names() == ["good_one"]
    assert "broken.py" in reg.load_errors


def test_hot_plug_new_file(tmp_path):
    d = tmp_path / "skills"
    d.mkdir()
    reg = load_skills_from_dir(d)
    assert reg.names() == []
    (d / "rea.py").write_text(
        'SKILL_NAME = "rea_skill"\nDESCRIPTION = "x"\n'
        'PARAMETERS = {"type": "object", "properties": {}}\n'
        "def run():\n    return 'rea'\n"
    )
    reg = load_skills_from_dir(d, reg)
    assert reg.call("rea_skill") == "rea"


def test_patch_applies_and_rejects_mismatch(workspace, registry):
    (workspace / "a.py").write_text("x = 1\ny = 2\n")
    good = "@@ -1,2 +1,2 @@\n x = 1\n-y = 2\n+y = 3\n"
    assert "patched" in registry.call("file_editor", {"path": "a.py", "patch": good})
    assert (workspace / "a.py").read_text() == "x = 1\ny = 3\n"
    bad = "@@ -1,2 +1,2 @@\n x = 1\n-y = 9\n+y = 4\n"
    out = registry.call("file_editor", {"path": "a.py", "patch": bad})
    assert out.startswith("ERROR")
    assert (workspace / "a.py").read_text() == "x = 1\ny = 3\n"


def test_path_escape_blocked(registry):
    out = registry.call("file_editor", {"path": "../../etc/passwd", "patch": "@@ -1 +1 @@\n-a\n+b\n"})
    assert "escapes workspace" in out


@pytest.mark.skipif(sys.platform == "win32", reason="bash runs on Linux only")
def test_bash_persistent_session(registry):
    first = registry.call("bash_terminal", {"command": "export KAGENT_X=42; cd /tmp >/dev/null; echo hi"})
    assert "hi" in first and "exit code 0" in first
    second = registry.call("bash_terminal", {"command": "echo $KAGENT_X"})
    assert "42" in second


@pytest.mark.skipif(sys.platform == "win32", reason="bash runs on Linux only")
def test_bash_timeout_restarts(registry):
    out = registry.call("bash_terminal", {"command": "sleep 5", "timeout": 1})
    assert "timed out" in out


def test_python_repl(registry):
    out = registry.call("python_repl", {"code": "print(2 + 3)"})
    assert "5" in out and "exit code: 0" in out


def test_file_explorer_ranks(workspace, registry):
    (workspace / "a.py").write_text("needle\nneedle\nneedle\n")
    (workspace / "b.py").write_text("needle\n")
    out = registry.call("file_explorer", {"pattern": "needle", "glob": "*.py"})
    assert out.index("a.py") < out.index("b.py")


def test_linter_autofixes_and_reports(workspace, registry):
    (workspace / "bad.py").write_text("import os\n")
    out = registry.call("linter", {"path": "bad.py"})
    assert "auto-fixes applied" in out
    assert (workspace / "bad.py").read_text() == ""  # unused import removed by ruff --fix
    assert "All checks passed" in out


def test_web_refuses_private_hosts(registry):
    out = registry.call("web_docs", {"action": "fetch", "url": "http://127.0.0.1:11434/api/tags"})
    assert "refused" in out


def test_web_refuses_non_http(registry):
    out = registry.call("web_docs", {"action": "fetch", "url": "file:///etc/passwd"})
    assert "only http" in out


def test_extract_json_from_prose():
    text = 'Sure! Here you go: ```json\n{"tool": "linter", "args": {"path": "a.py"}}\n```'
    assert extract_json(text, ("tool",))["tool"] == "linter"


def test_worker_role_gate(registry):
    llm = ScriptedLLM(['{"tool": "bash_terminal", "args": {"command": "rm -rf /"}}', '{"final": "done"}'])
    res = run_worker("researcher", "x", llm, "m", registry)
    assert res.ok
    assert "not available" in res.steps[0]["observation"]


def test_worker_step_budget(registry):
    llm = ScriptedLLM(['{"tool": "python_repl", "args": {"code": "print(1)"}}'])
    res = run_worker("executor", "x", llm, "m", registry, max_steps=2)
    assert not res.ok


def test_graph_end_to_end_with_retry(workspace, registry, monkeypatch):
    monkeypatch.setenv("KAGENT_MAX_ROUNDS", "2")
    plan = json.dumps({"subtasks": [{"role": "executor", "task": "print 5"}, {"role": "bogus", "task": "x"}]})
    worker_final = '{"final": "5"}'
    judge_reject = '{"ok": false, "feedback": "show the output"}'
    judge_accept = '{"ok": true, "feedback": ""}'
    synth = "The answer is 5."
    # Call order: plan, worker(final), judge(reject), worker(final), judge(accept), synth
    llm = ScriptedLLM([plan, worker_final, judge_reject, worker_final, judge_accept, synth])
    from core.config import get_settings

    graph = build_graph(llm, registry, get_settings())
    state = run_request(graph, "what is 5?", model="qwen2.5-coder:7b")
    assert state["answer"] == "The answer is 5."
    roles = [r["role"] for r in state["results"]]
    assert roles.count("executor") == 2  # one retry round
    assert any(e["type"] == "retry" for e in state["events"])
    assert any(a["status"] == "accepted" for a in state["accepted"])


def test_unresolved_marked_when_rounds_exhausted(workspace, registry, monkeypatch):
    plan = json.dumps({"subtasks": [{"role": "researcher", "task": "find docs"}]})
    fail = '{"ok": false, "feedback": "no"}'
    llm = ScriptedLLM([plan, '{"final": "maybe"}', fail, '{"final": "maybe"}', fail, "partial answer"])
    from core.config import get_settings

    state = run_request(build_graph(llm, registry, get_settings()), "docs?", model="llama3.1:8b")
    assert any(a["status"] == "unresolved" for a in state["accepted"])
    assert state["answer"] == "partial answer"


def test_disallowed_model_rejected():
    from core.llm import OllamaEngine

    with pytest.raises(ValueError):
        OllamaEngine()._client("some-random:model")
