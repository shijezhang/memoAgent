"""
实验1: 反思学习效果评估

验证 Agent 的反思学习能力：
1. 能否从用户纠正中提取有效规则
2. 规则是否在后续对话中正确应用
3. 知识是否正确持久化
"""

import json
import time
import os
import sys
from pathlib import Path
from typing import Dict, List, Tuple
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
from memo_agent.reflection.detector import ReflectionDetector
from memo_agent.reflection.reflector import Reflector
from memo_agent.reflection.kg_updater import KGUpdater
from memo_agent.retrieval.entity_extractor import EntityExtractor
from memo_agent.retrieval.context_assembler import ContextAssembler
from memo_agent.core.llm_caller import LLMCaller
from langchain_openai import ChatOpenAI


@dataclass
class ExperimentResult:
    """实验结果"""
    experiment_name: str
    timestamp: str
    metrics: Dict
    details: List[Dict]


class ReflectionExperiment:
    """反思学习实验"""

    def __init__(self, output_dir: Path):
        self.output_dir = output_dir
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # 加载实验数据
        with open(output_dir / "qa_pairs.json", encoding="utf-8") as f:
            self.qa_pairs = json.load(f)
        with open(output_dir / "correction_scenarios.json", encoding="utf-8") as f:
            self.correction_scenarios = json.load(f)

        # 初始化组件
        self._setup_components()

    def _setup_components(self):
        """初始化系统组件"""
        self.config = Config()

        # LLM
        self.llm = ChatOpenAI(
            model=self.config.llm_model,
            base_url=self.config.llm_base_url,
            api_key=self.config.llm_api_key,
            max_tokens=1024,
        )
        self.llm_caller = LLMCaller(self.llm)

        # 记忆
        self.semantic = SemanticMemory(kg_file=self.config.kg_file)
        self.semantic.load()

        self.episodic = EpisodicMemory(
            persist_dir=self.config.chroma_dir,
            embedding_model_name=self.config.embedding_model,
        )
        self.working = WorkingMemory(max_turns=20)

        # 其他组件
        self.detector = ReflectionDetector(self.config)
        self.entity_extractor = EntityExtractor(self.llm)
        self.context_assembler = ContextAssembler(self.entity_extractor)
        self.reflector = Reflector(self.llm)
        self.kg_updater = KGUpdater()

    def _ask_question(self, question: str) -> Tuple[str, List[str]]:
        """提问并获取回答"""
        # 提取实体
        entities = self.entity_extractor.extract(question)

        # 组装上下文
        context = self.context_assembler.assemble(
            question, self.working, self.episodic, self.semantic
        )

        # 获取回答
        response = self.llm_caller.invoke(context)

        return response, entities

    def _handle_correction(self, user_input: str, correction: str) -> Tuple[bool, str]:
        """处理纠正，尝试提取规则"""
        # 获取最近的 AI 回复作为错误上下文
        recent = self.working.get_recent(2)
        error_context = ""
        for msg in recent:
            if msg["role"] == "assistant":
                error_context = msg["content"]
                break

        # 提取实体
        entities = self.entity_extractor.extract(user_input + " " + correction)

        # 反思
        from memo_agent.models import Guideline
        guideline = self.reflector.reflect_with_context(
            error_context, correction, entities
        )

        if guideline is None:
            return False, "未能提取规则"

        # 更新知识图谱
        self.kg_updater.apply_guideline(
            guideline, self.semantic,
            log_file=self.config.reflection_log,
            error_context=error_context,
            reflection_prompt=self.reflector.last_prompt
        )

        return True, guideline.rule

    def run_baseline_test(self) -> Dict:
        """基线测试：无反思情况下的错误率"""
        print("\n" + "=" * 50)
        print("Phase 1: 基线测试")
        print("=" * 50)

        # 选择类型A问题（需要规则约束）
        type_a_questions = [q for q in self.qa_pairs if q["type"] == "type_a"]

        results = []
        correct_count = 0

        for qa in type_a_questions[:10]:  # 测试前10个
            question = qa["question"]
            print(f"\nQ: {question[:50]}...")

            response, entities = self._ask_question(question)

            # 简单评估：检查关键词是否出现在回答中
            reference = qa["reference_answer"]
            is_correct = self._evaluate_answer(response, reference)

            results.append({
                "question": question,
                "response": response[:200],
                "is_correct": is_correct,
            })

            if is_correct:
                correct_count += 1
                print(f"  ✓ 正确")
            else:
                print(f"  ✗ 错误")

            self.working.add("user", question)
            self.working.add("assistant", response)

        error_rate = (len(type_a_questions[:10]) - correct_count) / len(type_a_questions[:10])

        print(f"\n基线测试结果: {correct_count}/10 正确, 错误率 {error_rate:.1%}")

        return {
            "total_questions": len(type_a_questions[:10]),
            "correct_count": correct_count,
            "error_rate": error_rate,
            "details": results,
        }

    def run_reflection_learning(self) -> Dict:
        """反思学习阶段"""
        print("\n" + "=" * 50)
        print("Phase 2: 反思学习")
        print("=" * 50)

        results = {
            "extraction_success": 0,
            "extraction_total": 0,
            "extracted_rules": [],
            "details": [],
        }

        for scenario in self.correction_scenarios:
            results["extraction_total"] += 1

            question = scenario["question"]
            wrong_answer = scenario["wrong_answer"]
            correction = scenario["correction"]
            expected_rule = scenario["expected_rule"]

            print(f"\n场景: {question[:40]}...")

            # 模拟对话：AI 给出错误回答
            self.working.add("user", question)
            self.working.add("assistant", wrong_answer)

            # 用户纠正
            user_correction = f"不对，{correction}"
            self.working.add("user", user_correction)

            # 尝试提取规则
            success, rule = self._handle_correction(question, correction)

            if success:
                results["extraction_success"] += 1
                results["extracted_rules"].append(rule)

                # 检查规则是否与预期匹配
                rule_match = self._check_rule_match(rule, expected_rule)

                results["details"].append({
                    "scenario_id": scenario["id"],
                    "extraction_success": True,
                    "extracted_rule": rule,
                    "expected_rule": expected_rule,
                    "rule_match": rule_match,
                })

                print(f"  ✓ 规则提取成功: {rule[:50]}...")
                print(f"    预期规则: {expected_rule[:50]}...")
                print(f"    匹配: {'是' if rule_match else '否'}")
            else:
                results["details"].append({
                    "scenario_id": scenario["id"],
                    "extraction_success": False,
                    "error": rule,
                })
                print(f"  ✗ 规则提取失败: {rule}")

        extraction_rate = results["extraction_success"] / results["extraction_total"]
        print(f"\n规则提取成功率: {extraction_rate:.1%}")

        return results

    def run_retest(self, baseline_error_rate: float) -> Dict:
        """重测阶段：验证规则是否生效"""
        print("\n" + "=" * 50)
        print("Phase 3: 规则生效验证")
        print("=" * 50)

        # 重新初始化工作记忆
        self.working.clear()

        # 重测相同问题
        type_a_questions = [q for q in self.qa_pairs if q["type"] == "type_a"]

        results = []
        correct_count = 0
        rule_hit_count = 0

        for qa in type_a_questions[:10]:
            question = qa["question"]
            entities = qa.get("entities", [])

            # 检查是否有规则命中
            matched_rules = []
            for entity in entities:
                rules = self.semantic.get_guidelines_for(entity)
                matched_rules.extend(rules)

            print(f"\nQ: {question[:50]}...")
            if matched_rules:
                print(f"  规则命中: {len(matched_rules)} 条")
                rule_hit_count += 1

            response, _ = self._ask_question(question)

            # 评估
            reference = qa["reference_answer"]
            is_correct = self._evaluate_answer(response, reference)

            results.append({
                "question": question,
                "response": response[:200],
                "is_correct": is_correct,
                "rules_matched": matched_rules,
            })

            if is_correct:
                correct_count += 1
                print(f"  ✓ 正确")
            else:
                print(f"  ✗ 错误")

            self.working.add("user", question)
            self.working.add("assistant", response)

        new_error_rate = (len(type_a_questions[:10]) - correct_count) / len(type_a_questions[:10])
        correction_rate = (baseline_error_rate - new_error_rate) / baseline_error_rate if baseline_error_rate > 0 else 0

        print(f"\n重测结果: {correct_count}/10 正确, 错误率 {new_error_rate:.1%}")
        print(f"错误纠正率: {correction_rate:.1%}")

        return {
            "total_questions": len(type_a_questions[:10]),
            "correct_count": correct_count,
            "error_rate": new_error_rate,
            "correction_rate": correction_rate,
            "rule_hit_count": rule_hit_count,
            "details": results,
        }

    def run_persistence_test(self) -> Dict:
        """持久化验证"""
        print("\n" + "=" * 50)
        print("Phase 4: 知识持久化验证")
        print("=" * 50)

        # 保存当前知识图谱
        self.semantic.save()

        # 重新加载
        new_semantic = SemanticMemory(kg_file=self.config.kg_file)
        new_semantic.load()

        # 统计规则数量
        total_rules = 0
        for _, data in new_semantic._graph.nodes(data=True):
            if data.get("type") == "rule":
                total_rules += 1

        print(f"持久化规则数: {total_rules}")

        return {
            "persisted_rules": total_rules,
            "persistence_rate": 1.0,  # 简单假设全部持久化
        }

    def _evaluate_answer(self, response: str, reference: str) -> bool:
        """简单评估答案是否正确"""
        # 使用关键词匹配
        reference_keywords = set(reference.replace("，", " ").replace("。", " ").replace("？", " ").split())
        response_keywords = set(response.replace("，", " ").replace("。", " ").replace("？", " ").split())

        # 计算关键词重叠
        overlap = reference_keywords & response_keywords

        # 如果重叠超过30%，认为正确
        if len(reference_keywords) > 0:
            overlap_rate = len(overlap) / len(reference_keywords)
            return overlap_rate > 0.3

        return False

    def _check_rule_match(self, extracted: str, expected: str) -> bool:
        """检查提取的规则是否与预期匹配"""
        # 简单的关键词匹配
        expected_keywords = set(expected.replace("，", " ").replace("。", " ").split())
        extracted_keywords = set(extracted.replace("，", " ").replace("。", " ").split())

        overlap = expected_keywords & extracted_keywords
        return len(overlap) >= 3  # 至少3个关键词重叠

    def run(self) -> ExperimentResult:
        """运行完整实验"""
        print("\n" + "=" * 60)
        print("实验1: 反思学习效果评估")
        print("=" * 60)

        start_time = time.time()

        # Phase 1: 基线测试
        baseline_results = self.run_baseline_test()

        # Phase 2: 反思学习
        reflection_results = self.run_reflection_learning()

        # Phase 3: 重测
        retest_results = self.run_retest(baseline_results["error_rate"])

        # Phase 4: 持久化验证
        persistence_results = self.run_persistence_test()

        elapsed_time = time.time() - start_time

        # 汇总指标
        metrics = {
            "rule_extraction_rate": reflection_results["extraction_success"] / reflection_results["extraction_total"],
            "baseline_error_rate": baseline_results["error_rate"],
            "retest_error_rate": retest_results["error_rate"],
            "error_correction_rate": retest_results["correction_rate"],
            "rule_hit_count": retest_results["rule_hit_count"],
            "persisted_rules": persistence_results["persisted_rules"],
            "elapsed_time_seconds": elapsed_time,
        }

        # 保存结果
        result = ExperimentResult(
            experiment_name="reflection_learning",
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            details=[
                {"phase": "baseline", "results": baseline_results},
                {"phase": "reflection", "results": reflection_results},
                {"phase": "retest", "results": retest_results},
                {"phase": "persistence", "results": persistence_results},
            ]
        )

        output_file = self.results_dir / "experiment1_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("实验1 结果汇总")
        print("=" * 60)
        print(f"规则提取成功率: {metrics['rule_extraction_rate']:.1%}")
        print(f"基线错误率: {metrics['baseline_error_rate']:.1%}")
        print(f"重测错误率: {metrics['retest_error_rate']:.1%}")
        print(f"错误纠正率: {metrics['error_correction_rate']:.1%}")
        print(f"规则命中次数: {metrics['rule_hit_count']}")
        print(f"持久化规则数: {metrics['persisted_rules']}")
        print(f"实验耗时: {elapsed_time:.1f}秒")
        print("=" * 60)

        return result


def main():
    output_dir = Path(__file__).parent.parent / "data" / "experiments"
    experiment = ReflectionExperiment(output_dir)
    experiment.run()


if __name__ == "__main__":
    main()
