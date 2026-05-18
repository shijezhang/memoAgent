# MemoAgent 实验执行计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to implement this plan task-by-task.

**Goal:** 执行3个核心实验，生成量化指标用于求职简历。

**Tech Stack:** Python 3.11 / DeepSeek API / ChromaDB / NetworkX

---

## Task 1: 创建实验框架和数据生成脚本

**Files:**
- Create: `experiments/__init__.py`
- Create: `experiments/generate_data.py`
- Create: `experiments/config.py`

**功能:**
1. 生成种子知识图谱（30个实体 + 20条规则）
2. 生成测试问答对（40个问题 + 标准答案）
3. 生成纠正场景（10个预设场景）

---

## Task 2: 实现实验1 - 反思学习效果评估

**Files:**
- Create: `experiments/run_experiment1.py`

**流程:**
1. 基线测试：无反思情况下回答30个问题
2. 反思学习：触发10次纠正，提取规则
3. 重测：相同问题，验证规则命中
4. 持久化验证：重启后检查规则

**指标:**
- 规则提取成功率
- 规则命中率
- 错误纠正率

---

## Task 3: 实现实验2 - 混合检索消融实验

**Files:**
- Create: `experiments/run_experiment2.py`
- Create: `experiments/evaluator.py`

**配置:**
- Baseline: 无KG无向量
- Vector-only: 仅向量检索
- KG-only: 仅知识图谱
- Hybrid: 完整系统

**评估:** GPT-4自动打分（准确性、完整性、相关性）

---

## Task 4: 实现实验3 - 系统性能基准测试

**Files:**
- Create: `experiments/run_experiment3.py`

**测试:**
- 单请求延迟（冷启动/热请求）
- 并发吞吐（1/5/10/20并发）
- 分段耗时分析
- 内存占用监控

---

## Task 5: 运行实验并生成报告

**Files:**
- Create: `experiments/analyze_results.py`
- Create: `docs/EXPERIMENT_REPORT.md`

**输出:**
- 实验结果JSON文件
- 实验报告Markdown
- 简历量化素材
