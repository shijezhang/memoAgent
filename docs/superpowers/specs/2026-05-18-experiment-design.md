# MemoAgent 实验设计与评估方案

> **目标**: 为求职简历提供量化数据支撑，验证 RAG系统、Agent架构、工程落地三个维度的能力。

---

## 1. 实验概览

| 实验 | 验证能力 | 核心指标 | 预计耗时 |
|------|----------|----------|----------|
| **实验1: 反思学习效果** | Agent架构 | 规则命中率、错误纠正率、知识沉淀数 | 4小时 |
| **实验2: 混合检索消融** | RAG系统 | 答案准确性(无/有KG、无/有向量) | 4小时 |
| **实验3: 系统性能基准** | 工程落地 | 延迟(P50/P95)、吞吐量、内存占用 | 2小时 |

---

## 2. 数据构建方案

### 2.1 种子知识图谱

**实体 (30个)**
```
架构类: Transformer, BERT, GPT, RNN, LSTM, CNN, Attention, Encoder, Decoder
模型类: RoBERTa, DistilBERT, T5, BART, LLaMA, GPT-4, Claude
技术类: Self-Attention, Positional Encoding, LayerNorm, Dropout
任务类: Text Classification, NER, QA, Summarization, Translation
```

**初始规则 (20条)**
```
1. Transformer的自注意力机制不改变序列长度
2. BERT使用双向编码，适用于理解任务
3. GPT使用单向解码，适用于生成任务
4. LayerNorm在Transformer中用于稳定训练
5. Positional Encoding为序列注入位置信息
...
```

### 2.2 测试问答对生成

**生成脚本**: 使用 DeepSeek API 自动生成

```python
# 问题模板
templates = [
    "请解释{entity}的核心原理",
    "{entity_a}和{entity_b}有什么区别？",
    "在{task}任务中，{entity}有什么优势？",
    "为什么{entity}需要{component}？",
    "{entity}的主要局限性是什么？",
]

# 生成流程
for template in templates:
    for entity_combination in sample_entities():
        question = template.format(**entity_combination)
        reference = llm.generate_answer(question)  # GPT-4 生成标准答案
        qa_pairs.append((question, reference))
```

**问题分类**:
- 类型A: 需要规则约束（10个）- 如"Transformer自注意力会影响序列长度吗？"
- 类型B: 需要历史上下文（10个）- 涉及之前讨论过的内容
- 类型C: 需要两者结合（10个）- 复杂推理问题
- 类型D: 通用知识（10个）- 无需外部信息

### 2.3 反思场景设计

**10个预设纠正场景**:

| 场景 | 错误回答 | 用户纠正 | 期望规则 |
|------|----------|----------|----------|
| 1 | "Transformer自注意力会把序列长度减半" | "不对，自注意力保持序列长度不变" | `Transformer自注意力保持序列长度` |
| 2 | "BERT可以用于文本生成" | "错了，BERT是双向编码器，不适合生成" | `BERT不适用于自回归生成任务` |
| 3 | "GPT是双向模型" | "不对，GPT是单向(从左到右)模型" | `GPT使用单向因果注意力` |
| ... | ... | ... | ... |

---

## 3. 实验1: 反思学习效果评估

### 3.1 实验目标

验证 Agent 的反思学习能力：
1. 能否从用户纠正中提取有效规则
2. 规则是否在后续对话中正确应用
3. 知识是否正确持久化

### 3.2 实验流程

```
Phase 1: 基线测试 (无反思)
├── 询问30个问题
├── 记录错误回答数量和类型
└── 统计基线错误率

Phase 2: 反思学习
├── Round 1-10: 触发10次纠正场景
│   ├── AI先给出错误回答
│   ├── 用户输入纠正
│   ├── 系统提取规则
│   └── 记录规则提取成功/失败
├── Round 11-30: 重测相同问题
│   ├── 统计规则命中情况
│   └── 记录错误修正情况
└── 计算改进指标

Phase 3: 持久化验证
├── 重启系统
├── 检查知识图谱文件
├── 验证规则是否加载成功
└── 重测5个关键问题
```

### 3.3 评估指标

| 指标 | 定义 | 计算公式 | 目标值 |
|------|------|----------|--------|
| **规则提取成功率** | 纠正后成功提取规则的比例 | `成功数 / 纠正次数` | ≥ 80% |
| **规则命中率** | 需要规则时正确应用的比例 | `命中数 / 需规则场景数` | ≥ 85% |
| **错误纠正率** | 反思后错误被修正的比例 | `(基线错误 - 反思后错误) / 基线错误` | ≥ 70% |
| **知识持久化率** | 重启后规则仍有效的比例 | `有效数 / 总规则数` | 100% |

### 3.4 成功标准

- 规则提取成功率 ≥ 80%
- 错误纠正率 ≥ 70%
- 规则命中率 ≥ 85%

---

## 4. 实验2: 混合检索消融实验

### 4.1 实验目标

量化知识图谱（KG）和向量检索各自对答案质量的贡献。

### 4.2 对比配置

| 配置 | KG检索 | 向量检索 | 工作记忆 | 说明 |
|------|--------|----------|----------|------|
| **Baseline** | ✗ | ✗ | ✓ | 仅当前对话上下文 |
| **Vector-only** | ✗ | ✓ | ✓ | 纯向量RAG |
| **KG-only** | ✓ | ✗ | ✓ | 纯知识图谱 |
| **Hybrid** | ✓ | ✓ | ✓ | 完整系统 |

### 4.3 实现方式

通过配置开关控制检索模块：

```python
class ContextAssembler:
    def assemble(self, user_input, working, episodic, semantic, 
                 use_kg=True, use_vector=True):
        sections = []
        
        if use_kg:
            # 知识图谱检索
            entities = self.extract_entities(user_input)
            guidelines = semantic.get_guidelines_for(entities)
            subgraph = semantic.get_subgraph(entities)
        
        if use_vector:
            # 向量检索
            history = episodic.search(user_input, top_k=3)
        
        # ...组装上下文
```

### 4.4 评估方法

**自动评估**: GPT-4 作为评判

```
评估Prompt:
你是学术回答质量评估专家。

问题: {question}
标准答案: {reference_answer}
模型回答: {model_response}

请从以下维度评分(每项1-5分):
1. 准确性: 事实是否正确
2. 完整性: 是否覆盖关键信息
3. 相关性: 是否切题

输出格式:
准确性: X分
完整性: X分
相关性: X分
总分: X分
简述理由: ...
```

### 4.5 评估指标

| 指标 | 定义 | 计算方式 |
|------|------|----------|
| **平均得分** | 40个问题的平均总分 | `sum(scores) / 40` |
| **类型A得分** | 需规则问题的平均分 | 验证KG贡献 |
| **类型B得分** | 需上下文问题的平均分 | 验证Vector贡献 |
| **类型C得分** | 需两者问题的平均分 | 验证协同效果 |
| **KG贡献度** | KG带来的提升占比 | `(Hybrid - Vector) / Hybrid` |
| **Vector贡献度** | Vector带来的提升占比 | `(Hybrid - KG) / Hybrid` |

### 4.6 成功标准

- Hybrid 配置平均分 ≥ 4.0
- 相比 Baseline 提升 ≥ 30%
- KG 和 Vector 各有显著贡献

---

## 5. 实验3: 系统性能基准测试

### 5.1 实验目标

测量系统的工程性能指标。

### 5.2 测试场景

**场景1: 单请求延迟**

```python
# 冷启动测试
restart_server()
response_time = measure_request(question)  # 首次请求

# 热请求测试
for _ in range(10):
    warm_up()
response_times = [measure_request(q) for q in test_questions]
```

**场景2: 并发吞吐**

```python
# 使用 locust 或自定义脚本
for concurrency in [1, 5, 10, 20]:
    with ThreadPoolExecutor(max_workers=concurrency) as executor:
        futures = [executor.submit(send_request, q) for q in questions]
        results = [f.result() for f in futures]
    record_metrics(concurrency, results)
```

**场景3: 记忆规模影响**

```python
# 向量库规模测试
for size in [100, 1000, 5000]:
    clear_and_populate_episodic(size)
    measure_search_latency()

# KG规模测试
for nodes in [50, 200, 500]:
    clear_and_populate_kg(nodes)
    measure_subgraph_retrieval_latency()
```

### 5.3 分段耗时分析

```python
# 记录各阶段耗时
def process_request(user_input):
    t0 = time.time()
    entities = entity_extractor.extract(user_input)  # 实体提取
    t1 = time.time()
    
    guidelines = semantic.get_guidelines(entities)    # KG检索
    t2 = time.time()
    
    history = episodic.search(user_input)            # 向量检索
    t3 = time.time()
    
    context = assembler.assemble(...)                # 上下文组装
    t4 = time.time()
    
    response = llm.invoke(context)                   # LLM调用
    t5 = time.time()
    
    return {
        "entity_extraction": t1 - t0,
        "kg_retrieval": t2 - t1,
        "vector_retrieval": t3 - t2,
        "context_assembly": t4 - t3,
        "llm_inference": t5 - t4,
        "total": t5 - t0,
    }
```

### 5.4 评估指标

| 指标 | 定义 | 目标值 |
|------|------|--------|
| **冷启动延迟** | 服务启动后首次请求时间 | < 3s |
| **P50延迟** | 50%请求的响应时间 | < 1s |
| **P95延迟** | 95%请求的响应时间 | < 2s |
| **QPS** | 单实例每秒处理请求数 | > 10 |
| **并发稳定性** | 并发20时P95延迟增长 | < 50% |
| **内存占用** | 稳定运行内存 | < 2GB |
| **实体提取耗时** | NER阶段延迟 | < 200ms |
| **KG检索耗时** | 子图提取延迟 | < 50ms |
| **向量检索耗时** | ChromaDB查询延迟 | < 100ms |
| **LLM调用耗时** | 模型推理延迟 | < 800ms |

---

## 6. 实现计划

### 6.1 脚本结构

```
experiments/
├── generate_data.py       # 数据生成脚本
│   ├── generate_kg()      # 生成知识图谱
│   ├── generate_qa()      # 生成问答对
│   └── generate_corrections()  # 生成纠正场景
├── run_experiment1.py     # 反思学习实验
├── run_experiment2.py     # 消融实验
├── run_experiment3.py     # 性能测试
├── evaluator.py           # 自动评估器
├── analyze_results.py     # 结果分析
└── results/
    ├── exp1_metrics.json
    ├── exp2_metrics.json
    └── exp3_metrics.json
```

### 6.2 执行顺序

```
Step 1: 数据准备 (30分钟)
├── 运行 generate_data.py
├── 生成知识图谱、问答对、纠正场景
└── 保存到 data/experiments/

Step 2: 实验1执行 (2小时)
├── 运行 run_experiment1.py
├── 自动化测试 + 记录指标
└── 生成 exp1_metrics.json

Step 3: 实验2执行 (2小时)
├── 运行 run_experiment2.py
├── 四种配置对比测试
└── GPT-4 自动评估

Step 4: 实验3执行 (1小时)
├── 运行 run_experiment3.py
├── 性能测试 + 记录指标
└── 生成分段耗时报告

Step 5: 结果分析 (30分钟)
├── 运行 analyze_results.py
├── 生成实验报告
└── 输出简历素材
```

---

## 7. 预期成果

### 7.1 实验报告

生成 `docs/EXPERIMENT_REPORT.md`，包含：
- 实验设计与配置
- 原始数据表格
- 指标统计结果
- 分析与结论

### 7.2 简历量化素材

**示例描述**:

> **MemoAgent - 具备反思学习能力的智能对话系统**
> 
> - 设计三层记忆架构（语义/情节/工作记忆），实现混合检索RAG系统
> - **反思学习实验**: 规则提取成功率 **85%**，错误纠正率 **73%**，规则命中率 **90%**
> - **消融实验**: 混合检索相比纯向量检索准确率提升 **25%**，KG贡献度 **40%**
> - **性能基准**: P95延迟 **1.2s**，单实例QPS **15**，内存占用 **1.5GB**
> - 技术栈: Python/FastAPI/LangChain/NetworkX/ChromaDB/React
