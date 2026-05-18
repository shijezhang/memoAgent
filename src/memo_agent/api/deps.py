import os
from functools import lru_cache
from dotenv import load_dotenv

load_dotenv()

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

_session_manager: SessionManager = None
_config: Config = None
_semantic: SemanticMemory = None
_episodic: EpisodicMemory = None


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


def init_app():
    global _session_manager, _config, _semantic, _episodic

    _config = Config()
    llm = _create_llm(_config)
    llm_caller = LLMCaller(llm, max_retries=_config.llm_max_retries, base_delay=_config.llm_retry_base_delay)

    _semantic = SemanticMemory(kg_file=_config.kg_file)
    _semantic.load()
    _episodic = EpisodicMemory(
        persist_dir=_config.chroma_dir,
        embedding_model_name=_config.embedding_model,
    )

    entity_extractor = EntityExtractor(llm)
    context_assembler = ContextAssembler(entity_extractor)
    reflector = Reflector(llm)
    kg_updater = KGUpdater()
    detector = ReflectionDetector(_config)
    working = WorkingMemory()

    agent_core = AgentCore(
        llm_caller=llm_caller,
        entity_extractor=entity_extractor,
        context_assembler=context_assembler,
        reflector=reflector,
        kg_updater=kg_updater,
        semantic=_semantic,
        episodic=_episodic,
    )

    _session_manager = SessionManager(
        config=_config,
        agent_core=agent_core,
        working=working,
        episodic=_episodic,
        semantic=_semantic,
        detector=detector,
    )


def get_session_manager() -> SessionManager:
    return _session_manager


def get_config() -> Config:
    return _config


def get_semantic() -> SemanticMemory:
    return _semantic


def get_episodic() -> EpisodicMemory:
    return _episodic
