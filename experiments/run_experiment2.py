"""
实验2: 混合检索消融实验

量化知识图谱（KG）和向量检索各自对答案质量的贡献
"""

import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent))

if not os.environ.get("DEEPSEEK_API_KEY"):
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")

from memo_agent.config import Config
from memo_agent.memory.semantic import SemanticMemory
from memo_agent.memory.episodic import EpisodicMemory
from memo_agent.memory.working import WorkingMemory
from memo_agent.retrieval.entity_extractor import EntityExtractor
from memo_agent.core.llm_caller import LLMCaller
from langchain_openai import ChatOpenAI


@dataclass
class ExperimentResult:
    experiment_name: str
    timestamp: str
    metrics: Dict
    details: List[Dict]


class RetrievalAblationExperiment:
    """混合检索消融实验"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # 加载问答对
        with open(output_dir / "qa_pairs.json", encoding="utf-8") as f:
            self.qa_pairs = json.load(f)

        # 初始化组件
        self._setup_components()

    def _setup_components(self):
        """初始化组件"""
        self.config = Config()

        self.llm = ChatOpenAI(
            model=self.config.llm_model,
            base_url=self.config.llm_base_url,
            api_key=self.config.llm_api_key,
            max_tokens=1024,
        )
        self.llm_caller = LLMCaller(self.llm)

        self.semantic = SemanticMemory(kg_file=self.config.kg_file)
        self.semantic.load()

        self.episodic = EpisodicMemory(
            persist_dir=self.config.chroma_dir,
            embedding_model_name=self.config.embedding_model,
        )

        self.entity_extractor = EntityExtractor(self.llm)

    def _assemble_context(
        self,
        user_input: str,
        working: WorkingMemory,
        use_kg: bool = True,
        use_vector: bool = True,
    ) -> str:
        """组装上下文，支持开关控制"""
        sections = []

        # System prompt
        system_prompt = """你是一个学术研究助手。
回复应当准确、简洁，使用中文回复。"""
        sections.append(system_prompt)

        # 提取实体
        entities = self.entity_extractor.extract(user_input)

        # KG 检索
        if use_kg and entities:
            # 获取规则
            all_guidelines = []
            for entity in entities:
                guidelines = self.semantic.get_guidelines_for(entity)
                all_guidelines.extend(guidelines)

            if all_guidelines:
                unique_guidelines = list(dict.fromkeys(all_guidelines))
                rule_text = "\n".join(f"- {g}" for g in unique_guidelines[:5])
                sections.append(f"【相关知识规则】\n{rule_text}")

            # 获取子图
            subgraph = self.semantic.get_subgraph(entities, depth=1)
            if subgraph["nodes"]:
                kg_parts = []
                for node in subgraph["nodes"][:10]:
                    kg_parts.append(f"- {node['name']} ({node.get('entity_type', node.get('type', ''))})")
                sections.append(f"【知识图谱】\n" + "\n".join(kg_parts))

        # 向量检索
        if use_vector:
            history = self.episodic.search(user_input, top_k=3)
            if history:
                history_parts = []
                for item in history[:3]:
                    history_parts.append(f"- {item['content'][:100]}...")
                sections.append(f"【相关历史】\n" + "\n".join(history_parts))

        # 工作记忆
        context = working.get_full_context()
        if context:
            conv_parts = []
            for msg in context[-6:]:  # 最近3轮
                role = "用户" if msg["role"] == "user" else "AI"
                conv_parts.append(f"{role}: {msg['content'][:100]}...")
            sections.append(f"【当前对话】\n" + "\n".join(conv_parts))

        sections.append(f"【用户问题】\n{user_input}")

        return "\n\n".join(sections)

    def _ask_with_config(
        self,
        question: str,
        working: WorkingMemory,
        use_kg: bool,
        use_vector: bool,
    ) -> str:
        """使用指定配置提问"""
        context = self._assemble_context(question, working, use_kg, use_vector)
        return self.llm_caller.invoke(context)

    def _evaluate_answer(self, response: str, reference: str) -> float:
        """评估答案质量 (1-5分)"""
        # 使用关键词匹配作为简单评估
        ref_words = set(reference.replace("，", " ").replace("。", " ").replace("？", " ").split())
        resp_words = set(response.replace("，", " ").replace("。", " ").replace("？", " ").split())

        if not ref_words:
            return 3.0

        overlap = ref_words & resp_words
        overlap_rate = len(overlap) / len(ref_words)

        # 映射到1-5分
        if overlap_rate > 0.5:
            return 5.0
        elif overlap_rate > 0.4:
            return 4.0
        elif overlap_rate > 0.3:
            return 3.0
        elif overlap_rate > 0.2:
            return 2.0
        else:
            return 1.0

    def run_config(
        self,
        config_name: str,
        use_kg: bool,
        use_vector: bool,
        questions: List[Dict],
    ) -> Dict:
        """运行单个配置"""
        print(f"\n运行配置: {config_name}")
        print(f"  KG: {'✓' if use_kg else '✗'}, Vector: {'✓' if use_vector else '✗'}")

        working = WorkingMemory(max_turns=20)
        scores = []
        type_scores = {"type_a": [], "type_b": [], "type_c": [], "type_d": []}

        for qa in questions:
            question = qa["question"]
            reference = qa["reference_answer"]
            qa_type = qa["type"]

            response = self._ask_with_config(question, working, use_kg, use_vector)
            score = self._evaluate_answer(response, reference)

            scores.append(score)
            type_scores[qa_type].append(score)

            working.add("user", question)
            working.add("assistant", response)

        avg_score = sum(scores) / len(scores)
        type_avg = {t: sum(s) / len(s) if s else 0 for t, s in type_scores.items()}

        print(f"  平均得分: {avg_score:.2f}")

        return {
            "config_name": config_name,
            "use_kg": use_kg,
            "use_vector": use_vector,
            "average_score": avg_score,
            "type_scores": type_avg,
            "total_questions": len(questions),
        }

    def run(self) -> ExperimentResult:
        """运行完整实验"""
        print("\n" + "=" * 60)
        print("实验2: 混合检索消融实验")
        print("=" * 60)

        start_time = time.time()

        # 选择测试问题
        test_questions = self.qa_pairs[:20]  # 每个配置测试20个问题

        # 四种配置
        configs = [
            ("Baseline (无检索)", False, False),
            ("Vector-only", False, True),
            ("KG-only", True, False),
            ("Hybrid (完整)", True, True),
        ]

        results = []
        for config_name, use_kg, use_vector in configs:
            result = self.run_config(config_name, use_kg, use_vector, test_questions)
            results.append(result)

        # 计算贡献度
        baseline_score = results[0]["average_score"]
        vector_score = results[1]["average_score"]
        kg_score = results[2]["average_score"]
        hybrid_score = results[3]["average_score"]

        # 贡献度计算
        kg_contribution = (hybrid_score - vector_score) / hybrid_score if hybrid_score > 0 else 0
        vector_contribution = (hybrid_score - kg_score) / hybrid_score if hybrid_score > 0 else 0

        # 相比基线的提升
        improvement_vs_baseline = (hybrid_score - baseline_score) / baseline_score if baseline_score > 0 else 0

        metrics = {
            "baseline_score": baseline_score,
            "vector_only_score": vector_score,
            "kg_only_score": kg_score,
            "hybrid_score": hybrid_score,
            "kg_contribution": kg_contribution,
            "vector_contribution": vector_contribution,
            "improvement_vs_baseline": improvement_vs_baseline,
            "elapsed_time_seconds": time.time() - start_time,
        }

        # 保存结果
        result = ExperimentResult(
            experiment_name="retrieval_ablation",
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            details=results,
        )

        output_file = self.results_dir / "experiment2_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("实验2 结果汇总")
        print("=" * 60)
        print(f"Baseline 得分: {baseline_score:.2f}")
        print(f"Vector-only 得分: {vector_score:.2f}")
        print(f"KG-only 得分: {kg_score:.2f}")
        print(f"Hybrid 得分: {hybrid_score:.2f}")
        print(f"KG 贡献度: {kg_contribution:.1%}")
        print(f"Vector 贡献度: {vector_contribution:.1%}")
        print(f"相比 Baseline 提升: {improvement_vs_baseline:.1%}")
        print("=" * 60)

        return result


def main():
    output_dir = Path(__file__).parent.parent / "data" / "experiments"
    experiment = RetrievalAblationExperiment(output_dir)
    experiment.run()


if __name__ == "__main__":
    main()
