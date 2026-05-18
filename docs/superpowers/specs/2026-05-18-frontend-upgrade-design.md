# MemoAgent 前端系统级升级设计规格

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 对 MemoAgent 前端进行系统级升级，打造类似 ChatGPT/Claude 的现代、专业、美观的用户界面。

**Architecture:** 基于 React 18 + TypeScript + Tailwind CSS，引入 Headless UI 提供专业交互组件，framer-motion 提供流畅动画，实现深色/浅色主题切换。

**Tech Stack:** React 18 / TypeScript / Tailwind CSS / Headless UI / Framer Motion / React Markdown / Lucide React

---

## 1. 技术栈与新增依赖

**新增依赖：**
```
@headlessui/react      # 专业交互组件（下拉菜单、对话框、切换等）
react-markdown         # Markdown 渲染
react-syntax-highlighter  # 代码高亮
framer-motion          # 流畅动画过渡
lucide-react           # 现代图标库（替代 emoji）
```

**技术架构：**
- 主题切换：Tailwind `dark:` 前缀 + `localStorage` 持久化
- 流式输出：WebSocket 连接后端 `/api/chat/ws` 端点
- 动画：framer-motion 提供 page transition、消息入场动画

---

## 2. 主题系统与颜色规范

**主题机制：**
- 顶部导航栏右侧放置主题切换按钮（太阳/月亮图标）
- 用户选择保存到 `localStorage`，刷新后保持
- 默认跟随系统偏好（`prefers-color-scheme`）

**颜色令牌：**

| 语义 | 浅色模式 | 深色模式 |
|------|----------|----------|
| 背景（主） | `#ffffff` | `#1a1a2e` |
| 背景（次） | `#f7f7f8` | `#16213e` |
| 背景（侧边栏） | `#f0f0f0` | `#0f0f23` |
| 文字（主） | `#1f2937` | `#e5e7eb` |
| 文字（次） | `#6b7280` | `#9ca3af` |
| 强调色 | `#3b82f6` (blue-500) | `#60a5fa` (blue-400) |
| 边框 | `#e5e7eb` | `#374151` |
| 用户消息气泡 | `#3b82f6` | `#2563eb` |
| AI 消息气泡 | `#f3f4f6` | `#1e293b` |

---

## 3. 布局与导航组件

### 3.1 顶部导航栏（新增）

- 高度：56px
- 左侧：应用 Logo + 名称 "MemoAgent"
- 右侧：主题切换按钮 + 设置图标（预留）
- 样式：浅色模式白色背景 + 底部阴影，深色模式深色背景 + 细边框

### 3.2 左侧边栏优化

- 宽度：64px（保持）
- 图标替换：emoji → lucide-react 图标
  - 对话：MessageCircle
  - 知识：Network
  - 记忆：Brain
  - 反思：ScrollText
- 激活态：背景色变化 + 左侧 3px 高亮条
- 悬停效果：背景色渐变过渡
- 底部添加「新建对话」按钮（Plus 图标）

### 3.3 状态栏优化

- 高度：32px
- 内容：模型名称 | KG 实体数 | Guidelines 数 | 当前会话 ID
- 浅色模式灰色背景，深色模式更深的背景
- 点击模型名称可展开模型信息（预留）

---

## 4. 对话页面

### 4.1 消息列表

- 用户消息：右对齐，蓝色背景，白色文字，圆角 16px（左侧圆角较小 4px）
- AI 消息：左对齐，浅灰/深色背景，深色文字，圆角 16px（右侧圆角较小 4px）
- 消息入场动画：淡入 + 轻微上移（framer-motion），持续 200ms
- 时间戳：消息下方浅色小字，悬停时显示

### 4.2 Markdown 渲染

- 代码块：语法高亮（react-syntax-highlighter）+ 复制按钮（右上角）
- 表格：响应式横向滚动
- 链接：新标签页打开
- 列表：适当缩进

### 4.3 流式输出

- 打字机效果：逐字符显示
- 光标闪烁：结尾处显示蓝色闪烁光标
- 思考状态：显示"思考中..."动画（三个点依次跳动）

### 4.4 输入区域

- 多行文本框，支持 Shift+Enter 换行
- 发送按钮：有内容时蓝色高亮，无内容时灰色禁用
- 停止按钮：AI 回复时显示红色停止按钮
- 底部提示：快捷键说明

---

## 5. 知识图谱页面

### 5.1 整体布局

- 主区域：深色背景（#0d1117），类似 Obsidian 的暗色调
- 右侧面板：保持浅色/深色跟随主题，宽度 280px

### 5.2 图谱可视化（Obsidian 风格）

**节点样式：**
- 实体节点：蓝色发光圆点，半径 6-12px（按连接数缩放）
- Guideline 节点：橙色发光圆点
- 悬停时：发光强度增加 + 显示名称标签
- 默认状态：节点标签隐藏，悬停或选中时显示

**连线样式：**
- 半透明蓝/橙色
- 粗细按关系类型区分
- 轻微脉动效果

**动画：**
- 节点缓慢漂浮
- 连线有轻微脉动效果

### 5.3 交互功能

- 鼠标拖拽：平移画布
- 滚轮：缩放
- 点击节点：高亮该节点及其一跳邻居，右侧面板显示详情
- 双击节点：以该节点为中心重新布局

### 5.4 右侧面板

- 搜索框：过滤节点
- 选中节点详情：名称、类型、关联节点列表
- 添加实体按钮
- 图例说明

---

## 6. 记忆状态页面

### 6.1 整体布局

- 页面标题 + 刷新按钮
- 三列卡片布局（保持现有结构）

### 6.2 卡片设计

- 圆角：12px
- 阴影：浅色模式下轻微阴影，深色模式下边框
- 标题栏：图标 + 标题，左对齐
- 内容区：数据以更大字号突出显示
- 操作按钮：清空按钮使用红色警示风格

### 6.3 Guidelines 列表

- 卡片式展示，每个 Guideline 一张卡片
- 橙色左边框标识
- 悬停时轻微抬起效果
- 支持搜索过滤

### 6.4 实体列表（新增）

- 在 Semantic Memory 卡片下方展开
- 标签云形式展示实体名称
- 点击实体可跳转到知识图谱页面并选中该节点

---

## 7. 反思日志页面

### 7.1 整体布局

- 顶部：标题 + 过滤器（实体搜索 + 时间范围 + 数量限制）
- 主体：时间线形式展示

### 7.2 时间线设计

- 左侧：竖向时间轴线，每个节点一个圆点
- 右侧：日志卡片
- 卡片内容：
  - 时间戳（顶部浅色小字）
  - Guideline 规则（主体内容，加粗显示）
  - 实体标签（蓝/橙色小标签）
  - 展开按钮

### 7.3 展开详情

- 错误上下文：红色背景区块
- 反思提示词：代码风格区块（等宽字体）
- KG 变更：绿色背景区块，显示新增节点/边数量
- 平滑展开/收起动画（framer-motion）

### 7.4 空状态

- 居中显示插图（简洁的线条图标）
- 提示文字："还没有反思记录，在对话中纠正 AI 来创建 Guidelines"

---

## 8. 文件结构

```
frontend/
├── src/
│   ├── components/
│   │   ├── Layout.tsx          # 重构：添加 Header
│   │   ├── Header.tsx          # 新增：顶部导航栏
│   │   ├── Sidebar.tsx         # 重构：图标 + 新建按钮
│   │   ├── StatusBar.tsx       # 优化样式
│   │   ├── ThemeToggle.tsx     # 新增：主题切换组件
│   │   └── ui/                 # 新增：通用 UI 组件
│   │       ├── Button.tsx
│   │       ├── Card.tsx
│   │       ├── Input.tsx
│   │       └── Badge.tsx
│   ├── pages/
│   │   ├── ChatPage.tsx        # 重构：流式 + Markdown
│   │   ├── KnowledgePage.tsx   # 重构：Obsidian 风格
│   │   ├── MemoryPage.tsx      # 优化样式
│   │   └── ReflectionPage.tsx  # 重构：时间线
│   ├── hooks/
│   │   ├── useTheme.ts         # 新增：主题管理
│   │   └── useWebSocket.ts     # 新增：WebSocket 流式
│   ├── lib/
│   │   └── cn.ts               # 新增：className 合并工具
│   └── index.css               # 扩展：主题 CSS 变量
├── tailwind.config.js          # 扩展：dark mode 配置
└── package.json                # 更新依赖
```

---

## 9. 实现优先级

1. **基础架构** - 主题系统、通用 UI 组件、图标库
2. **布局组件** - Header、Sidebar 重构、StatusBar 优化
3. **对话页面** - Markdown 渲染、流式输出、消息动画
4. **知识图谱** - Obsidian 风格可视化、交互优化
5. **记忆页面** - 卡片样式、实体列表
6. **反思页面** - 时间线布局、展开详情
