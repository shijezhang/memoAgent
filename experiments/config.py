"""
实验配置：种子数据、问题模板、纠正场景
"""

# 种子知识图谱实体
SEED_ENTITIES = [
    # 架构类
    {"name": "Transformer", "type": "architecture", "description": "基于自注意力的序列模型架构"},
    {"name": "BERT", "type": "model", "description": "双向编码器表示模型"},
    {"name": "GPT", "type": "model", "description": "生成式预训练Transformer"},
    {"name": "RNN", "type": "architecture", "description": "循环神经网络"},
    {"name": "LSTM", "type": "architecture", "description": "长短期记忆网络"},
    {"name": "CNN", "type": "architecture", "description": "卷积神经网络"},
    {"name": "Attention", "type": "mechanism", "description": "注意力机制"},
    {"name": "Self-Attention", "type": "mechanism", "description": "自注意力机制"},
    {"name": "Encoder", "type": "component", "description": "编码器"},
    {"name": "Decoder", "type": "component", "description": "解码器"},

    # 模型类
    {"name": "RoBERTa", "type": "model", "description": "优化版BERT"},
    {"name": "DistilBERT", "type": "model", "description": "蒸馏版BERT"},
    {"name": "T5", "type": "model", "description": "文本到文本迁移Transformer"},
    {"name": "BART", "type": "model", "description": "双向自回归Transformer"},
    {"name": "LLaMA", "type": "model", "description": "大规模语言模型"},
    {"name": "GPT-4", "type": "model", "description": "GPT系列第四代模型"},

    # 技术组件
    {"name": "Positional Encoding", "type": "component", "description": "位置编码"},
    {"name": "LayerNorm", "type": "component", "description": "层归一化"},
    {"name": "Dropout", "type": "technique", "description": "随机失活正则化"},
    {"name": "Residual Connection", "type": "technique", "description": "残差连接"},
    {"name": "Multi-Head Attention", "type": "mechanism", "description": "多头注意力"},

    # 任务类
    {"name": "Text Classification", "type": "task", "description": "文本分类任务"},
    {"name": "NER", "type": "task", "description": "命名实体识别"},
    {"name": "Question Answering", "type": "task", "description": "问答任务"},
    {"name": "Summarization", "type": "task", "description": "文本摘要任务"},
    {"name": "Translation", "type": "task", "description": "机器翻译任务"},
    {"name": "Language Modeling", "type": "task", "description": "语言建模"},

    # 概念类
    {"name": "Pre-training", "type": "concept", "description": "预训练"},
    {"name": "Fine-tuning", "type": "concept", "description": "微调"},
    {"name": "Transfer Learning", "type": "concept", "description": "迁移学习"},
    {"name": "Tokenization", "type": "concept", "description": "分词"},
]

# 种子规则（用于测试规则命中）
SEED_GUIDELINES = [
    {"rule": "Transformer的自注意力机制保持序列长度不变，只改变特征维度", "entities": ["Transformer", "Self-Attention"]},
    {"rule": "BERT使用双向编码，适用于理解类任务，不适用于自回归生成", "entities": ["BERT", "Encoder"]},
    {"rule": "GPT使用单向（从左到右）因果注意力，适用于文本生成任务", "entities": ["GPT", "Decoder"]},
    {"rule": "Positional Encoding为Transformer注入位置信息，因为自注意力无位置感知", "entities": ["Transformer", "Positional Encoding"]},
    {"rule": "LayerNorm在Transformer中用于稳定训练，通常在每个子层后应用", "entities": ["Transformer", "LayerNorm"]},
    {"rule": "RNN存在梯度消失问题，LSTM通过门控机制缓解此问题", "entities": ["RNN", "LSTM"]},
    {"rule": "Transformer相比RNN的主要优势是并行计算能力", "entities": ["Transformer", "RNN"]},
    {"rule": "Multi-Head Attention允许模型同时关注不同位置的不同表示子空间", "entities": ["Multi-Head Attention", "Attention"]},
    {"rule": "BERT的[CLS] token用于分类任务，[SEP] token用于分隔句子对", "entities": ["BERT"]},
    {"rule": "GPT系列模型的参数量与性能通常呈幂律关系", "entities": ["GPT"]},
    {"rule": "T5将所有NLP任务统一为文本到文本格式", "entities": ["T5"]},
    {"rule": "DistilBERT通过知识蒸馏将BERT压缩约40%，保持97%性能", "entities": ["DistilBERT", "BERT"]},
    {"rule": "RoBERTa相比BERT使用更大批次和更多训练数据", "entities": ["RoBERTa", "BERT"]},
    {"rule": "预训练-微调范式是现代NLP的主流方法", "entities": ["Pre-training", "Fine-tuning"]},
    {"rule": "Transfer Learning允许模型将学到的知识迁移到下游任务", "entities": ["Transfer Learning"]},
]

# 问题模板
QUESTION_TEMPLATES = {
    # 类型A: 需要规则约束
    "type_a": [
        "{entity_a}的自注意力机制会改变序列长度吗？",
        "{entity_a}可以用于文本生成任务吗？",
        "{entity_a}和{entity_b}的主要区别是什么？",
        "为什么{entity}需要Positional Encoding？",
        "{entity_a}相比{entity_b}有什么优势？",
    ],
    # 类型B: 需要历史上下文（需要预存对话）
    "type_b": [
        "根据我们之前讨论的内容，{entity}的核心原理是什么？",
        "你刚才提到的{entity}，能再详细解释一下吗？",
        "关于{entity}，我之前问过的问题你还记得吗？",
    ],
    # 类型C: 需要两者结合
    "type_c": [
        "基于{entity_a}的特点，它适合用于{task}任务吗？为什么？",
        "如果要用{entity}做{task}，需要注意什么问题？",
        "{entity_a}和{entity_b}哪个更适合{task}任务？请分析原因。",
    ],
    # 类型D: 通用知识
    "type_d": [
        "请简单介绍一下{entity}。",
        "{entity}的主要特点是什么？",
        "{entity}在NLP领域有什么应用？",
        "{entity}的发展历史是怎样的？",
    ],
}

# 纠正场景（用于反思学习实验）
CORRECTION_SCENARIOS = [
    {
        "question": "Transformer的自注意力机制会把序列长度变成多少？",
        "wrong_answer": "Transformer的自注意力机制会将序列长度减半，因为每个位置只关注一半的位置。",
        "correction": "不对，Transformer的自注意力机制保持序列长度不变，输出的序列长度与输入相同。",
        "expected_rule": "Transformer的自注意力机制保持序列长度不变",
        "entities": ["Transformer", "Self-Attention"],
    },
    {
        "question": "BERT可以用于文本生成任务吗？",
        "wrong_answer": "可以的，BERT是一个非常强大的模型，可以用于各种文本生成任务，包括故事创作、文章续写等。",
        "correction": "错了，BERT是双向编码器，它会看到完整的输入，所以不适用于需要自回归生成的文本生成任务。",
        "expected_rule": "BERT不适用于自回归文本生成任务",
        "entities": ["BERT", "Encoder"],
    },
    {
        "question": "GPT是什么类型的模型？",
        "wrong_answer": "GPT是一个双向模型，可以同时看到前后文的上下文信息。",
        "correction": "不对，GPT是单向（从左到右）的因果语言模型，只能看到当前位置之前的上下文。",
        "expected_rule": "GPT使用单向因果注意力，只能看到左侧上下文",
        "entities": ["GPT", "Decoder"],
    },
    {
        "question": "Transformer为什么需要Positional Encoding？",
        "wrong_answer": "Positional Encoding主要是为了增加模型参数量，让模型更强大。",
        "correction": "不对，Positional Encoding是因为自注意力机制本身没有位置感知能力，需要额外注入位置信息。",
        "expected_rule": "自注意力机制无位置感知，Positional Encoding用于注入位置信息",
        "entities": ["Self-Attention", "Positional Encoding"],
    },
    {
        "question": "RNN和LSTM有什么区别？",
        "wrong_answer": "RNN和LSTM基本上是一样的，只是LSTM参数更多。",
        "correction": "不对，LSTM引入了门控机制（遗忘门、输入门、输出门），专门解决RNN的梯度消失问题。",
        "expected_rule": "LSTM通过门控机制解决RNN的梯度消失问题",
        "entities": ["RNN", "LSTM"],
    },
    {
        "question": "Transformer相比RNN的并行能力如何？",
        "wrong_answer": "Transformer和RNN都需要顺序计算，并行能力差不多。",
        "correction": "不对，Transformer的最大优势就是可以完全并行计算，而RNN必须顺序处理。",
        "expected_rule": "Transformer可以完全并行计算，RNN必须顺序处理",
        "entities": ["Transformer", "RNN"],
    },
    {
        "question": "Multi-Head Attention的作用是什么？",
        "wrong_answer": "Multi-Head Attention只是为了增加计算量，让模型看起来更复杂。",
        "correction": "不对，Multi-Head Attention允许模型同时关注不同位置的不同的表示子空间，增强表达能力。",
        "expected_rule": "Multi-Head Attention让模型同时关注多个表示子空间",
        "entities": ["Multi-Head Attention", "Attention"],
    },
    {
        "question": "T5的设计理念是什么？",
        "wrong_answer": "T5是为翻译任务设计的，只能做机器翻译。",
        "correction": "不对，T5的核心设计是将所有NLP任务统一为文本到文本格式，用同一个模型处理所有任务。",
        "expected_rule": "T5将所有NLP任务统一为文本到文本格式",
        "entities": ["T5"],
    },
    {
        "question": "DistilBERT和BERT是什么关系？",
        "wrong_answer": "DistilBERT是BERT的升级版，参数更多，效果更好。",
        "correction": "不对，DistilBERT是通过知识蒸馏压缩的BERT，参数更少（约减少40%），但保持了约97%的性能。",
        "expected_rule": "DistilBERT通过知识蒸馏压缩BERT，减少40%参数保持97%性能",
        "entities": ["DistilBERT", "BERT"],
    },
    {
        "question": "预训练和微调是什么关系？",
        "wrong_answer": "预训练和微调是两种完全独立的技术，没有关系。",
        "correction": "不对，预训练-微调是一个范式：先在大规模数据上预训练，再在特定任务上微调。",
        "expected_rule": "预训练-微调是两阶段范式：大规模预训练后任务特定微调",
        "entities": ["Pre-training", "Fine-tuning"],
    },
]

# 实体关系（用于知识图谱）
ENTITY_RELATIONS = [
    ("Transformer", "variant_of", "BERT"),
    ("Transformer", "variant_of", "GPT"),
    ("Transformer", "variant_of", "T5"),
    ("BERT", "optimized_by", "RoBERTa"),
    ("BERT", "compressed_to", "DistilBERT"),
    ("Transformer", "uses", "Self-Attention"),
    ("Transformer", "uses", "Positional Encoding"),
    ("Transformer", "uses", "LayerNorm"),
    ("Self-Attention", "extension_of", "Attention"),
    ("Multi-Head Attention", "type_of", "Attention"),
    ("LSTM", "improves", "RNN"),
    ("Transformer", "advantage_over", "RNN"),
    ("BERT", "suitable_for", "NER"),
    ("BERT", "suitable_for", "Text Classification"),
    ("GPT", "suitable_for", "Language Modeling"),
    ("T5", "suitable_for", "Translation"),
    ("T5", "suitable_for", "Summarization"),
]
