"""
实验3: 系统性能基准测试

测量系统的工程性能指标：
- 延迟分布 (P50/P95)
- 吞吐量 (QPS)
- 分段耗时分析
- 内存占用
"""

import json
import time
import os
import sys
import statistics
import tracemalloc
from pathlib import Path
from typing import Dict, List
from dataclasses import dataclass, asdict
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

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
from memo_agent.retrieval.context_assembler import ContextAssembler
from memo_agent.core.llm_caller import LLMCaller
from langchain_openai import ChatOpenAI


@dataclass
class ExperimentResult:
    experiment_name: str
    timestamp: str
    metrics: Dict
    details: List[Dict]


class PerformanceBenchmark:
    """性能基准测试"""

    def __init__(self):
        self.results_dir = Path(__file__).parent / "results"
        self.results_dir.mkdir(parents=True, exist_ok=True)

        # 加载测试问题
        qa_file = Path(__file__).parent.parent / "data" / "experiments" / "qa_pairs.json"
        with open(qa_file, encoding="utf-8") as f:
            self.qa_pairs = json.load(f)

        self._setup_components()

    def _setup_components(self):
        """初始化组件"""
        self.config = Config()

        self.llm = ChatOpenAI(
            model=self.config.llm_model,
            base_url=self.config.llm_base_url,
            api_key=self.config.llm_api_key,
            max_tokens=512,  # 减少输出长度加速测试
        )
        self.llm_caller = LLMCaller(self.llm)

        self.semantic = SemanticMemory(kg_file=self.config.kg_file)
        self.semantic.load()

        self.episodic = EpisodicMemory(
            persist_dir=self.config.chroma_dir,
            embedding_model_name=self.config.embedding_model,
        )

        self.entity_extractor = EntityExtractor(self.llm)
        self.context_assembler = ContextAssembler(self.entity_extractor)

    def measure_single_request(self, question: str) -> Dict:
        """测量单次请求的详细耗时"""
        working = WorkingMemory(max_turns=10)

        timings = {}

        # 实体提取
        t0 = time.time()
        entities = self.entity_extractor.extract(question)
        timings["entity_extraction"] = time.time() - t0

        # KG 检索
        t1 = time.time()
        guidelines = []
        for entity in entities:
            guidelines.extend(self.semantic.get_guidelines_for(entity))
        subgraph = self.semantic.get_subgraph(entities, depth=1)
        timings["kg_retrieval"] = time.time() - t1

        # 向量检索
        t2 = time.time()
        history = self.episodic.search(question, top_k=3)
        timings["vector_retrieval"] = time.time() - t2

        # 上下文组装
        t3 = time.time()
        context = self.context_assembler.assemble(
            question, working, self.episodic, self.semantic
        )
        timings["context_assembly"] = time.time() - t3

        # LLM 调用
        t4 = time.time()
        response = self.llm_caller.invoke(context)
        timings["llm_inference"] = time.time() - t4

        timings["total"] = time.time() - t0

        return {
            "question": question[:50],
            "timings": timings,
            "response_length": len(response),
        }

    def benchmark_latency(self, num_requests: int = 20) -> Dict:
        """延迟基准测试"""
        print("\n" + "=" * 50)
        print("延迟基准测试")
        print("=" * 50)

        questions = [q["question"] for q in self.qa_pairs[:num_requests]]
        latencies = []
        detailed_results = []

        # 冷启动（首次请求）
        print("\n冷启动测试...")
        cold_start = self.measure_single_request(questions[0])
        print(f"  冷启动延迟: {cold_start['timings']['total']:.2f}s")

        # 热请求
        print("\n热请求测试...")
        for i, question in enumerate(questions[1:]):
            result = self.measure_single_request(question)
            latencies.append(result["timings"]["total"])
            detailed_results.append(result)
            print(f"  请求 {i+1}: {result['timings']['total']:.2f}s")

        # 统计
        sorted_latencies = sorted(latencies)
        p50 = statistics.median(latencies)
        p95 = sorted_latencies[int(len(sorted_latencies) * 0.95)] if len(sorted_latencies) > 20 else sorted_latencies[-1]
        avg = statistics.mean(latencies)

        # 分段耗时统计
        segment_times = {
            "entity_extraction": [],
            "kg_retrieval": [],
            "vector_retrieval": [],
            "context_assembly": [],
            "llm_inference": [],
        }
        for result in detailed_results:
            for key in segment_times:
                segment_times[key].append(result["timings"].get(key, 0))

        segment_avg = {k: statistics.mean(v) for k, v in segment_times.items()}

        print(f"\n延迟统计:")
        print(f"  P50: {p50:.2f}s")
        print(f"  P95: {p95:.2f}s")
        print(f"  平均: {avg:.2f}s")

        print(f"\n分段耗时:")
        for segment, t in segment_avg.items():
            print(f"  {segment}: {t*1000:.0f}ms")

        return {
            "cold_start_latency": cold_start["timings"]["total"],
            "p50_latency": p50,
            "p95_latency": p95,
            "avg_latency": avg,
            "segment_times": segment_avg,
            "total_requests": len(latencies),
        }

    def benchmark_throughput(self, concurrency_levels: List[int] = [1, 5, 10]) -> Dict:
        """吞吐量测试"""
        print("\n" + "=" * 50)
        print("吞吐量测试")
        print("=" * 50)

        questions = [q["question"] for q in self.qa_pairs[:15]]
        results = {}

        for concurrency in concurrency_levels:
            print(f"\n并发级别: {concurrency}")

            start_time = time.time()
            completed = 0
            latencies = []

            with ThreadPoolExecutor(max_workers=concurrency) as executor:
                futures = []
                for i in range(concurrency * 2):  # 每个并发执行2次
                    question = questions[i % len(questions)]
                    future = executor.submit(self.measure_single_request, question)
                    futures.append(future)

                for future in as_completed(futures):
                    try:
                        result = future.result(timeout=60)
                        latencies.append(result["timings"]["total"])
                        completed += 1
                    except Exception as e:
                        print(f"  请求失败: {e}")

            elapsed = time.time() - start_time
            qps = completed / elapsed if elapsed > 0 else 0

            results[f"concurrency_{concurrency}"] = {
                "completed": completed,
                "elapsed": elapsed,
                "qps": qps,
                "avg_latency": statistics.mean(latencies) if latencies else 0,
            }

            print(f"  完成: {completed} 请求")
            print(f"  耗时: {elapsed:.2f}s")
            print(f"  QPS: {qps:.2f}")
            print(f"  平均延迟: {results[f'concurrency_{concurrency}']['avg_latency']:.2f}s")

        return results

    def benchmark_memory(self) -> Dict:
        """内存占用测试"""
        print("\n" + "=" * 50)
        print("内存占用测试")
        print("=" * 50)

        tracemalloc.start()

        # 测量组件加载后的内存
        working = WorkingMemory(max_turns=50)

        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        print(f"  当前内存: {current / 1024 / 1024:.1f} MB")
        print(f"  峰值内存: {peak / 1024 / 1024:.1f} MB")

        return {
            "current_mb": current / 1024 / 1024,
            "peak_mb": peak / 1024 / 1024,
        }

    def run(self) -> ExperimentResult:
        """运行完整基准测试"""
        print("\n" + "=" * 60)
        print("实验3: 系统性能基准测试")
        print("=" * 60)

        start_time = time.time()

        # 延迟测试
        latency_results = self.benchmark_latency(15)

        # 吞吐量测试
        throughput_results = self.benchmark_throughput([1, 5])

        # 内存测试
        memory_results = self.benchmark_memory()

        elapsed = time.time() - start_time

        # 汇总指标
        metrics = {
            "p50_latency": latency_results["p50_latency"],
            "p95_latency": latency_results["p95_latency"],
            "cold_start_latency": latency_results["cold_start_latency"],
            "qps_single": throughput_results.get("concurrency_1", {}).get("qps", 0),
            "qps_concurrent_5": throughput_results.get("concurrency_5", {}).get("qps", 0),
            "memory_peak_mb": memory_results["peak_mb"],
            "entity_extraction_ms": latency_results["segment_times"]["entity_extraction"] * 1000,
            "kg_retrieval_ms": latency_results["segment_times"]["kg_retrieval"] * 1000,
            "vector_retrieval_ms": latency_results["segment_times"]["vector_retrieval"] * 1000,
            "llm_inference_ms": latency_results["segment_times"]["llm_inference"] * 1000,
            "elapsed_time_seconds": elapsed,
        }

        result = ExperimentResult(
            experiment_name="performance_benchmark",
            timestamp=datetime.now().isoformat(),
            metrics=metrics,
            details=[
                {"test": "latency", "results": latency_results},
                {"test": "throughput", "results": throughput_results},
                {"test": "memory", "results": memory_results},
            ]
        )

        # 保存结果
        output_file = self.results_dir / "experiment3_results.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(asdict(result), f, ensure_ascii=False, indent=2)

        print("\n" + "=" * 60)
        print("实验3 结果汇总")
        print("=" * 60)
        print(f"P50 延迟: {metrics['p50_latency']:.2f}s")
        print(f"P95 延迟: {metrics['p95_latency']:.2f}s")
        print(f"冷启动延迟: {metrics['cold_start_latency']:.2f}s")
        print(f"单并发 QPS: {metrics['qps_single']:.2f}")
        print(f"5并发 QPS: {metrics['qps_concurrent_5']:.2f}")
        print(f"峰值内存: {metrics['memory_peak_mb']:.1f} MB")
        print(f"实体提取: {metrics['entity_extraction_ms']:.0f}ms")
        print(f"KG 检索: {metrics['kg_retrieval_ms']:.0f}ms")
        print(f"向量检索: {metrics['vector_retrieval_ms']:.0f}ms")
        print(f"LLM 推理: {metrics['llm_inference_ms']:.0f}ms")
        print("=" * 60)

        return result


def main():
    benchmark = PerformanceBenchmark()
    benchmark.run()


if __name__ == "__main__":
    main()
