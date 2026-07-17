# MemoAgent

一个具备**长期记忆**和**反思学习能力**的智能对话代理系统。

## 核心特性

- **多级记忆系统**: 语义记忆（知识图谱）+ 情节记忆（向量检索）+ 工作记忆（会话管理）
- **反思学习**: 从用户纠正中自动提取推理规则，持久化并在后续对话中应用
- **混合检索**: 结合知识图谱子图查询和向量相似度检索
- **实时对话**: 基于 WebSocket 的流式响应

## 技术栈

**后端**
- Python 3.11+
- FastAPI + Uvicorn
- LangChain + LangChain-Anthropic/OpenAI
- ChromaDB (向量存储)
- NetworkX (知识图谱)

**前端**
- React 18 + TypeScript
- Tailwind CSS + Framer Motion
- Headless UI
- Vite

## 快速开始

### 环境准备

1. 克隆项目
```bash
git clone https://github.com/shijezhang/memoAgent.git
cd memoAgent
```

2. 安装后端依赖
```bash
pip install -e ".[dev]"
```

3. 配置环境变量
```bash
cp .env.example .env
# 编辑 .env 并填入你的 API Key
```

4. 安装前端依赖
```bash
cd frontend
npm install
cd ..
```

### 运行项目

**方式一: Docker Compose（推荐）**
```bash
docker-compose up
```

**方式二: 本地开发**

启动后端:
```bash
uvicorn memo_agent.api.app:app --reload --host 0.0.0.0 --port 8000
```

启动前端:
```bash
cd frontend
npm run dev
```

访问 `http://localhost:5173` 开始对话。

## 项目结构

```
memoAgent/
├── src/memo_agent/          # 后端核心代码
│   ├── core/                # Agent 核心逻辑
│   ├── memory/              # 三级记忆模块
│   ├── retrieval/           # 混合检索
│   ├── reflection/          # 反思学习
│   └── api/                 # FastAPI 接口
├── frontend/                # React 前端
├── experiments/             # 实验代码与结果
├── docs/                    # 技术文档
├── tests/                   # 单元测试
└── data/                    # 数据目录（gitignore）
```

## 实验结果

系统通过三组实验验证了核心能力：

| 实验 | 验证能力 | 核心指标 |
|------|----------|----------|
| 实验1: 反思学习 | Agent架构 | 规则提取成功率 100%、规则命中 9次 |
| 实验2: 混合检索消融 | RAG系统 | KG检索 1ms、向量检索 31ms |
| 实验3: 系统性能基准 | 工程落地 | 分段耗时分析、检索效率验证 |

详细报告见 [EXPERIMENT_REPORT.md](docs/EXPERIMENT_REPORT.md) 和 [TECHNICAL_REPORT.md](docs/TECHNICAL_REPORT.md)。

## 运行测试

```bash
pytest tests/
```

## 许可证

MIT License

## 作者

张世杰 ([@shijezhang](https://github.com/shijezhang))
