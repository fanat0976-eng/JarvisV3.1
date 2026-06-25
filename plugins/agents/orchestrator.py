"""
Orchestrator — Главный агент, делегирует задачи подагентам.
Анализирует запрос, выбирает агента, выполняет, возвращает результат.
"""
import re
import httpx

from plugins.agents.registry import get_agent, classify_task, Agent

_ORCHESTRATOR_MODEL = "qwen2.5:14b"

def _load_config_model():
    global _ORCHESTRATOR_MODEL
    try:
        import yaml
        from pathlib import Path
        config_path = Path(__file__).parent.parent.parent / "core" / "config.yaml"
        with open(config_path) as f:
            config = yaml.safe_load(f)
        _ORCHESTRATOR_MODEL = config.get("ollama", {}).get("default_model", _ORCHESTRATOR_MODEL)
    except Exception:
        pass

_load_config_model()


def _build_system_prompt(agent: Agent, task: str) -> str:
    base = agent.system_prompt
    tools_text = "\n".join(f"- {t}" for t in agent.tools)
    return f"{base}\n\nДоступные инструменты:\n{tools_text}\n\nДля вызова инструмента ответь в формате:\n<<<TOOL_CALL>>>\ntool: <название>\n<параметры>\n<<<END_TOOL_CALL>>>"


async def _call_ollama(model: str, messages: list[dict], temperature: float = 0.7,
                        timeout: int = 300) -> str:
    payload = {
        "model": model,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature, "top_p": 0.9, "num_predict": 4096},
    }
    async with httpx.AsyncClient(trust_env=False, timeout=timeout) as client:
        r = await client.post("http://localhost:11434/api/chat", json=payload)
        r.raise_for_status()
        return r.json().get("message", {}).get("content", "")


def _parse_tool_calls(text: str) -> list[str]:
    pattern = r'<<<TOOL_CALL>>>(.*?)<<<END_TOOL_CALL>>>'
    return re.findall(pattern, text, re.DOTALL)


def _execute_tool(tool_str: str) -> dict:
    from plugins.brain.tool_executor import execute_tool_call
    return execute_tool_call(tool_str)


async def run_agent(
    agent_name: str,
    task: str,
    context: list[dict] | None = None,
    tool_executor=None,
) -> dict:
    agent = get_agent(agent_name)
    if not agent:
        return {"status": "error", "error": f"Agent '{agent_name}' not found"}

    system_prompt = _build_system_prompt(agent, task)
    messages = [{"role": "system", "content": system_prompt}]

    if context:
        messages.extend(context[-10:])

    messages.append({"role": "user", "content": task})

    all_results = []
    iteration = 0

    while iteration < agent.max_iterations:
        try:
            reply = await _call_ollama(
                agent.model, messages, agent.temperature, timeout=300
            )
        except Exception as e:
            return {"status": "error", "error": str(e), "agent": agent_name, "iterations": iteration}

        tool_calls = _parse_tool_calls(reply)
        if not tool_calls:
            clean_reply = re.sub(r'<<<TOOL_CALL>>>.*?<<<END_TOOL_CALL>>>', '', reply, flags=re.DOTALL).strip()
            return {
                "status": "ok",
                "agent": agent_name,
                "model": agent.model,
                "reply": clean_reply,
                "tool_results": all_results,
                "iterations": iteration + 1,
            }

        for tc in tool_calls:
            result = _execute_tool(tc)
            all_results.append(result)

        tool_summary = "\n".join(
            f"[{r.get('tool', '?')}] {'OK' if r.get('status') == 'ok' else 'ERROR'}: "
            + str(r.get('text', r.get('error', r.get('path', r.get('items', '')))))[:500]
            for r in all_results
        )

        messages.append({"role": "assistant", "content": reply})
        messages.append({"role": "user", "content": f"Результаты инструментов:\n{tool_summary}\n\nПродолжи."})
        iteration += 1

    clean_reply = re.sub(r'<<<TOOL_CALL>>>.*?<<<END_TOOL_CALL>>>', '', reply, flags=re.DOTALL).strip()
    return {
        "status": "ok",
        "agent": agent_name,
        "model": agent.model,
        "reply": clean_reply,
        "tool_results": all_results,
        "iterations": iteration,
    }


async def orchestrate(task: str, context: list[dict] | None = None) -> dict:
    agent_name = classify_task(task)
    if agent_name == "orchestrator":
        return await _run_orchestrator(task, context)
    return await run_agent(agent_name, task, context)


async def _run_orchestrator(task: str, context: list[dict] | None = None) -> dict:
    from plugins.agents.registry import get_agent
    _ = get_agent("orchestrator") or get_agent("research")

    system_prompt = (
        "Ты — оркестратор Jarvis. Проанализируй задачу и выполни её самостоятельно. "
        "Если задача простая — ответь напрямую. "
        "Если нужен код — используй инструменты файлов. "
        "Если нужен поиск — используй web/search или rag/search."
    )
    messages = [{"role": "system", "content": system_prompt}]
    if context:
        messages.extend(context[-10:])
    messages.append({"role": "user", "content": task})

    try:
        reply = await _call_ollama(_ORCHESTRATOR_MODEL, messages, 0.5, timeout=300)
    except Exception as e:
        return {"status": "error", "error": str(e), "agent": "orchestrator"}

    return {
        "status": "ok",
        "agent": "orchestrator",
        "model": _ORCHESTRATOR_MODEL,
        "reply": reply.strip(),
        "tool_results": [],
        "iterations": 1,
    }
