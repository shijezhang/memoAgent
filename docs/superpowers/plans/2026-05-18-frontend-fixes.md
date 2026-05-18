# 前端功能修复计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 修复三个前端功能问题：设置图标无响应、新建对话按钮无响应、模型回复非流式输出。

**Architecture:** 在现有 React 组件基础上添加缺失的功能实现。

---

## Task 1: 修复设置图标功能

**Files:**
- Modify: `frontend/src/components/Header.tsx`
- Create: `frontend/src/components/SettingsModal.tsx`

**问题描述:**
设置图标点击后没有反应，需要添加设置弹窗。

**解决方案:**
创建一个设置弹窗组件，包含基本的设置选项（如 API 配置、模型选择等预留功能），点击设置图标时打开弹窗。

**步骤:**
1. 创建 `SettingsModal.tsx` 组件，使用 Headless UI 的 Dialog 组件
2. 在 Header.tsx 中添加状态控制弹窗显示/隐藏
3. 点击设置图标时打开弹窗

---

## Task 2: 修复新建对话按钮功能

**Files:**
- Modify: `frontend/src/components/Sidebar.tsx`
- Modify: `frontend/src/store/useStore.ts`

**问题描述:**
左下角 "+" 图标点击无反应，应该清空当前对话并开始新会话。

**解决方案:**
1. 在 useStore 中添加 `clearMessages` 和 `resetSession` 方法
2. 在 Sidebar 中实现点击 "+" 按钮时调用这些方法

**步骤:**
1. 在 useStore.ts 添加 `clearMessages` action
2. 在 Sidebar.tsx 中导入并调用该方法
3. 添加确认提示或直接清空

---

## Task 3: 实现流式输出

**Files:**
- Modify: `frontend/src/pages/ChatPage.tsx`
- Modify: `backend/src/memo_agent/api/routes/chat.py` (如果需要)

**问题描述:**
当前模型回复是直接给出所有答案，需要实现逐字流式输出效果。

**解决方案:**
由于后端当前使用同步 API 调用，先在前端实现模拟流式输出效果（打字机效果），后续可升级为真正的 WebSocket 流式输出。

**步骤:**
1. 在 ChatPage 中添加打字机效果函数
2. 收到 AI 回复后，逐字符添加到显示内容
3. 添加速度控制（如每 30ms 输出一个字符）
4. 支持在流式输出时点击停止按钮中断

---

## 执行顺序

1. Task 1: 设置图标 → 创建设置弹窗
2. Task 2: 新建对话 → 清空消息功能
3. Task 3: 流式输出 → 打字机效果
