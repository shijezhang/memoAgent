import sys
import logging

from dotenv import load_dotenv

from memo_agent.config import Config
from memo_agent.orchestrator import Orchestrator

load_dotenv()

HELP_TEXT = """可用命令：
  /help              显示帮助
  /quit              退出并保存
  /reflect           手动触发反思
  /memory status     显示三级记忆状态
  /memory clear episodic  清空情节记忆
  /guidelines        列出所有已沉淀的 Guidelines
"""


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    config = Config()

    from langchain_anthropic import ChatAnthropic
    llm = ChatAnthropic(model=config.llm_model, max_tokens=4096)

    orch = Orchestrator(config=config, llm=llm)
    orch.start_session()

    print("MemoAgent 已启动。输入 /help 查看命令，/quit 退出。")

    try:
        from prompt_toolkit import prompt as pt_prompt
        use_prompt_toolkit = True
    except ImportError:
        use_prompt_toolkit = False

    while True:
        try:
            if use_prompt_toolkit:
                user_input = pt_prompt("User >> ").strip()
            else:
                user_input = input("User >> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break

        if not user_input:
            continue

        if user_input == "/quit":
            print("再见！")
            break

        if user_input == "/help":
            print(HELP_TEXT)
            continue

        if user_input == "/guidelines":
            _print_guidelines(orch)
            continue

        if user_input == "/memory status":
            _print_memory_status(orch)
            continue

        if user_input == "/memory clear episodic":
            orch.episodic.clear()
            print("情节记忆已清空。")
            continue

        if user_input == "/reflect":
            try:
                correction = input("请输入纠正内容: ").strip()
            except (EOFError, KeyboardInterrupt):
                continue
            if correction:
                user_input = f"不对，{correction}"
            else:
                continue

        response = orch.run_turn(user_input)
        print(f"Agent >> {response}")


def _print_memory_status(orch: Orchestrator):
    entity_count = sum(1 for _, d in orch.semantic._graph.nodes(data=True) if d.get("type") == "entity")
    rule_count = sum(1 for _, d in orch.semantic._graph.nodes(data=True) if d.get("type") == "rule")
    try:
        conv_count = orch.episodic._collection.count()
    except Exception:
        conv_count = 0
    print(f"语义记忆: {entity_count} 个实体, {rule_count} 条 Guidelines")
    print(f"情节记忆: {conv_count} 条对话记录")
    print(f"工作记忆: {len(orch.working.get_full_context())} 轮当前对话")


def _print_guidelines(orch: Orchestrator):
    rules = []
    for _, data in orch.semantic._graph.nodes(data=True):
        if data.get("type") == "rule":
            rules.append(data.get("rule", ""))
    if not rules:
        print("暂无 Guidelines。")
        return
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule}")


if __name__ == "__main__":
    main()
