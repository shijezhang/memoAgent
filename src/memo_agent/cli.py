import sys
import logging

from dotenv import load_dotenv

from memo_agent.config import Config
from memo_agent.core.agent import AgentCore
from memo_agent.core.llm_caller import LLMCaller
from memo_agent.core.session import SessionManager
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.memory.working import WorkingMemory
from memo_agent.reflection.detector import ReflectionDetector
from memo_agent.reflection.kg_updater import KGUpdater
from memo_agent.reflection.reflector import Reflector
from memo_agent.retrieval.context_assembler import ContextAssembler
from memo_agent.retrieval.entity_extractor import EntityExtractor

load_dotenv()

HELP_TEXT = """可用命令：
  /help              显示帮助
  /quit              退出并保存
  /reflect           手动触发反思
  /memory status     显示三级记忆状态
  /memory clear episodic  清空情节记忆
  /guidelines        列出所有已沉淀的 Guidelines
"""


def _create_llm(config: Config):
    if config.llm_provider == "deepseek":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(
            model=config.llm_model,
            base_url=config.llm_base_url,
            api_key=config.llm_api_key,
            max_tokens=4096,
        )
    elif config.llm_provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=config.llm_model, max_tokens=4096)
    else:
        raise ValueError(f"Unknown LLM provider: {config.llm_provider}")


def main():
    logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")

    config = Config()
    llm = _create_llm(config)
    llm_caller = LLMCaller(llm, max_retries=config.llm_max_retries, base_delay=config.llm_retry_base_delay)

    semantic = SemanticMemory(kg_file=config.kg_file)
    semantic.load()
    episodic = EpisodicMemory(
        persist_dir=config.chroma_dir,
        embedding_model_name=config.embedding_model,
    )

    entity_extractor = EntityExtractor(llm)
    context_assembler = ContextAssembler(entity_extractor)
    reflector = Reflector(llm)
    kg_updater = KGUpdater()
    detector = ReflectionDetector(config)
    working = WorkingMemory()

    agent_core = AgentCore(
        llm_caller=llm_caller,
        entity_extractor=entity_extractor,
        context_assembler=context_assembler,
        reflector=reflector,
        kg_updater=kg_updater,
        semantic=semantic,
        episodic=episodic,
    )

    session = SessionManager(
        config=config,
        agent_core=agent_core,
        working=working,
        episodic=episodic,
        semantic=semantic,
        detector=detector,
    )

    session.start_session()

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
            _print_guidelines(semantic)
            continue

        if user_input == "/memory status":
            _print_memory_status(session, semantic, episodic)
            continue

        if user_input == "/memory clear episodic":
            episodic.clear()
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

        result = session.process_turn(user_input)
        print(f"Agent >> {result.response}")


def _print_memory_status(session: SessionManager, semantic: SemanticMemory, episodic: EpisodicMemory):
    entity_count = sum(1 for _, d in semantic._graph.nodes(data=True) if d.get("type") == "entity")
    rule_count = sum(1 for _, d in semantic._graph.nodes(data=True) if d.get("type") == "rule")
    try:
        conv_count = episodic._collection.count()
    except Exception:
        conv_count = 0
    print(f"语义记忆: {entity_count} 个实体, {rule_count} 条 Guidelines")
    print(f"情节记忆: {conv_count} 条对话记录")
    print(f"工作记忆: {len(session._working.get_full_context())} 轮当前对话")


def _print_guidelines(semantic: SemanticMemory):
    rules = []
    for _, data in semantic._graph.nodes(data=True):
        if data.get("type") == "rule":
            rules.append(data.get("rule", ""))
    if not rules:
        print("暂无 Guidelines。")
        return
    for i, rule in enumerate(rules, 1):
        print(f"  {i}. {rule}")


if __name__ == "__main__":
    main()
