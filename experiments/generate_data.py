"""
数据生成脚本：生成知识图谱、测试问答对、纠正场景数据
"""

import json
import random
import hashlib
from pathlib import Path
from typing import List, Dict, Tuple

# 添加当前目录到路径
import sys
sys.path.insert(0, str(Path(__file__).parent))

from config import (
    SEED_ENTITIES, SEED_GUIDELINES, QUESTION_TEMPLATES,
    CORRECTION_SCENARIOS, ENTITY_RELATIONS
)


def generate_knowledge_graph(output_dir: Path) -> Dict:
    """生成种子知识图谱"""
    kg = {
        "nodes": [],
        "edges": []
    }

    # 添加实体节点
    for entity in SEED_ENTITIES:
        node_id = f"entity_{entity['name'].replace(' ', '_').replace('-', '_')}"
        kg["nodes"].append({
            "id": node_id,
            "type": "entity",
            "name": entity["name"],
            "entity_type": entity["type"],
            "description": entity["description"]
        })

    # 添加规则节点
    for i, guideline in enumerate(SEED_GUIDELINES):
        rule_id = f"rule_{i}"
        kg["nodes"].append({
            "id": rule_id,
            "type": "rule",
            "name": guideline["rule"][:50],
            "rule": guideline["rule"]
        })

        # 添加 governing 边
        for entity_name in guideline["entities"]:
            entity_id = f"entity_{entity_name.replace(' ', '_').replace('-', '_')}"
            kg["edges"].append({
                "source": entity_id,
                "target": rule_id,
                "type": "governs"
            })

    # 添加实体关系边
    for source, relation, target in ENTITY_RELATIONS:
        source_id = f"entity_{source.replace(' ', '_').replace('-', '_')}"
        target_id = f"entity_{target.replace(' ', '_').replace('-', '_')}"
        kg["edges"].append({
            "source": source_id,
            "target": target_id,
            "type": relation
        })

    # 保存
    output_file = output_dir / "seed_kg.json"
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(kg, f, ensure_ascii=False, indent=2)

    print(f"✓ 生成知识图谱: {len(kg['nodes'])} 节点, {len(kg['edges'])} 边")
    return kg


def generate_qa_pairs(output_dir: Path) -> List[Dict]:
    """生成测试问答对"""
    qa_pairs = []

    # 获取实体名称列表
    entity_names = [e["name"] for e in SEED_ENTITIES]
    task_names = [e["name"] for e in SEED_ENTITIES if e["type"] == "task"]

    qa_id = 0

    # 类型A: 需要规则约束 (10个)
    type_a_questions = [
        ("Transformer", "Self-Attention", "Transformer的自注意力机制会改变序列长度吗？",
         "不会。Transformer的自注意力机制保持序列长度不变，输出的序列长度与输入相同，只改变特征维度。"),
        ("BERT", None, "BERT可以用于文本生成任务吗？",
         "BERT不适合用于文本生成任务。BERT是双向编码器，它会同时看到整个输入序列，无法进行自回归生成。文本生成通常使用GPT等单向解码器模型。"),
        ("GPT", None, "GPT使用什么类型的注意力？",
         "GPT使用单向（从左到右）的因果注意力，每个位置只能看到当前位置及其之前的内容，适合自回归文本生成。"),
        ("Transformer", "Positional Encoding", "为什么Transformer需要Positional Encoding？",
         "因为自注意力机制本身没有位置感知能力，它对输入序列中元素的顺序不敏感。Positional Encoding为每个位置添加唯一的位置向量，使模型能够区分不同位置的元素。"),
        ("Transformer", "RNN", "Transformer相比RNN的主要优势是什么？",
         "Transformer的主要优势是可以完全并行计算，不像RNN需要顺序处理。这使得Transformer在训练时能更好地利用GPU并行能力，大幅提高训练效率。"),
        ("LSTM", "RNN", "LSTM是如何改进RNN的？",
         "LSTM通过引入门控机制（遗忘门、输入门、输出门）来解决RNN的梯度消失问题，使模型能够更好地学习长期依赖关系。"),
        ("Multi-Head Attention", None, "Multi-Head Attention的作用是什么？",
         "Multi-Head Attention允许模型同时关注不同位置的不同表示子空间。每个注意力头可以学习关注不同类型的信息，最后将这些信息合并，增强模型的表达能力。"),
        ("T5", None, "T5的设计理念是什么？",
         "T5的核心设计理念是将所有NLP任务统一为文本到文本格式。无论是分类、翻译、摘要还是问答，都转换为输入文本到输出文本的形式，使用同一个模型处理。"),
        ("DistilBERT", "BERT", "DistilBERT和BERT有什么关系？",
         "DistilBERT是通过知识蒸馏技术从BERT压缩得到的轻量级模型。它的参数量约为BERT的60%，但保持了约97%的性能，推理速度更快。"),
        ("Pre-training", "Fine-tuning", "预训练-微调范式是什么？",
         "预训练-微调是一种迁移学习范式。首先在大规模无标注数据上预训练模型，学习通用语言表示；然后在特定任务的标注数据上微调，使模型适应下游任务。"),
    ]

    for entity_a, entity_b, question, answer in type_a_questions:
        qa_pairs.append({
            "id": f"qa_{qa_id}",
            "type": "type_a",
            "question": question,
            "reference_answer": answer,
            "entities": [e for e in [entity_a, entity_b] if e],
            "requires_rule": True,
        })
        qa_id += 1

    # 类型B: 需要历史上下文 (10个) - 模拟预存对话
    type_b_contexts = [
        ("我们之前讨论过Transformer的并行计算能力。", "Transformer为什么比RNN更快？",
         "如之前讨论的，Transformer可以完全并行计算，不像RNN需要顺序处理每个时间步。这使得Transformer能够充分利用GPU并行能力，大幅加速训练过程。"),
        ("刚才提到BERT是双向编码器。", "那么BERT适合做什么任务？",
         "如前所述，BERT作为双向编码器，非常适合理解类任务，如文本分类、命名实体识别、情感分析等，因为它能同时看到整个输入的上下文信息。"),
        ("我们讨论过GPT的单向特性。", "GPT的这种设计有什么优缺点？",
         "GPT的单向因果注意力使其非常适合文本生成，因为生成过程本质上是从左到右的。缺点是无法利用双向上下文信息，在理解类任务上不如BERT。"),
    ]

    for context, question, answer in type_b_contexts:
        qa_pairs.append({
            "id": f"qa_{qa_id}",
            "type": "type_b",
            "question": question,
            "reference_answer": answer,
            "context": context,
            "entities": [],
            "requires_history": True,
        })
        qa_id += 1

    # 扩展类型B到10个
    for i in range(7):
        entity = random.choice(entity_names)
        qa_pairs.append({
            "id": f"qa_{qa_id}",
            "type": "type_b",
            "question": f"关于{entity}，你能结合之前的讨论再详细说明一下吗？",
            "reference_answer": f"基于之前的讨论，{entity}是NLP领域的重要概念。具体细节需要参考之前的对话上下文。",
            "entities": [entity],
            "requires_history": True,
        })
        qa_id += 1

    # 类型C: 需要两者结合 (10个)
    type_c_questions = [
        ("BERT", "Question Answering", "BERT适合用于问答任务吗？为什么？",
         "BERT非常适合问答任务。作为双向编码器，它能同时理解问题和文章的上下文，通过预测答案的起始和结束位置来抽取答案。这是BERT的典型应用场景之一。"),
        ("GPT", "Summarization", "GPT适合用于文本摘要任务吗？",
         "GPT适合文本摘要任务。摘要生成可以建模为条件文本生成，GPT的单向生成能力使其能够流畅地生成摘要文本。不过纯GPT可能需要适当的提示工程来获得好的效果。"),
        ("Transformer", "RNN", "Translation", "Transformer和RNN哪个更适合机器翻译？为什么？",
         "Transformer更适合机器翻译。它的并行计算能力使训练更高效，自注意力机制能直接建模任意位置的依赖关系，更适合处理长距离依赖，这对翻译质量很重要。"),
    ]

    for entity_a, entity_b, task, question, answer in [(q[0], q[1], None, q[2], q[3]) if len(q) == 4 else (q[0], None, q[1], q[2], q[3]) for q in type_c_questions]:
        entities = [e for e in [entity_a, entity_b] if e]
        qa_pairs.append({
            "id": f"qa_{qa_id}",
            "type": "type_c",
            "question": question,
            "reference_answer": answer,
            "entities": entities,
            "requires_rule": True,
            "requires_history": False,
        })
        qa_id += 1

    # 扩展类型C到10个
    for i in range(7):
        entity = random.choice(entity_names[:10])  # 主要模型
        task = random.choice(task_names) if task_names else "NLP任务"
        qa_pairs.append({
            "id": f"qa_{qa_id}",
            "type": "type_c",
            "question": f"{entity}适合用于{task}吗？请分析原因。",
            "reference_answer": f"这需要结合{entity}的架构特点和{task}的任务需求来分析。具体适用性取决于任务的性质和模型的设计。",
            "entities": [entity],
            "requires_rule": True,
        })
        qa_id += 1

    # 类型D: 通用知识 (10个)
    for entity in random.sample(entity_names, 10):
        qa_pairs.append({
            "id": f"qa_{qa_id}",
            "type": "type_d",
            "question": f"请简要介绍一下{entity}。",
            "reference_answer": f"{entity}是自然语言处理领域的重要概念。",
            "entities": [entity],
            "requires_rule": False,
        })
        qa_id += 1

    # 保存
    output_file = output_dir / "qa_pairs.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(qa_pairs, f, ensure_ascii=False, indent=2)

    print(f"✓ 生成问答对: {len(qa_pairs)} 个")
    return qa_pairs


def generate_correction_scenarios(output_dir: Path) -> List[Dict]:
    """生成纠正场景数据"""
    scenarios = []

    for i, scenario in enumerate(CORRECTION_SCENARIOS):
        scenarios.append({
            "id": f"correction_{i}",
            "question": scenario["question"],
            "wrong_answer": scenario["wrong_answer"],
            "correction": scenario["correction"],
            "expected_rule": scenario["expected_rule"],
            "entities": scenario["entities"],
        })

    # 保存
    output_file = output_dir / "correction_scenarios.json"
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(scenarios, f, ensure_ascii=False, indent=2)

    print(f"✓ 生成纠正场景: {len(scenarios)} 个")
    return scenarios


def main():
    """主函数"""
    output_dir = Path(__file__).parent.parent / "data" / "experiments"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 50)
    print("MemoAgent 实验数据生成")
    print("=" * 50)

    # 生成知识图谱
    kg = generate_knowledge_graph(output_dir)

    # 生成问答对
    qa_pairs = generate_qa_pairs(output_dir)

    # 生成纠正场景
    scenarios = generate_correction_scenarios(output_dir)

    # 生成统计信息
    stats = {
        "kg_nodes": len(kg["nodes"]),
        "kg_edges": len(kg["edges"]),
        "kg_rules": len([n for n in kg["nodes"] if n["type"] == "rule"]),
        "qa_total": len(qa_pairs),
        "qa_type_a": len([q for q in qa_pairs if q["type"] == "type_a"]),
        "qa_type_b": len([q for q in qa_pairs if q["type"] == "type_b"]),
        "qa_type_c": len([q for q in qa_pairs if q["type"] == "type_c"]),
        "qa_type_d": len([q for q in qa_pairs if q["type"] == "type_d"]),
        "correction_scenarios": len(scenarios),
    }

    stats_file = output_dir / "data_stats.json"
    with open(stats_file, "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 50)
    print("数据统计:")
    print(f"  知识图谱: {stats['kg_nodes']} 节点, {stats['kg_edges']} 边, {stats['kg_rules']} 规则")
    print(f"  问答对: {stats['qa_total']} 个")
    print(f"    - 类型A (需规则): {stats['qa_type_a']}")
    print(f"    - 类型B (需上下文): {stats['qa_type_b']}")
    print(f"    - 类型C (需两者): {stats['qa_type_c']}")
    print(f"    - 类型D (通用): {stats['qa_type_d']}")
    print(f"  纠正场景: {stats['correction_scenarios']} 个")
    print("=" * 50)


if __name__ == "__main__":
    main()
