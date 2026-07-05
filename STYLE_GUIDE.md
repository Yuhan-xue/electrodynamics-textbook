# 后期修改规范

> 本文件规定了本教材后续修改时应遵从的排版、物理、内容三层规范。
> 任何修改者（包括 AI 和人工）在提交变更前，应逐项核对此清单。

---

## 一、物理严谨性规范

### 1.1 公式与符号

| 检查项 | 要求 |
|--------|------|
| 矢量粗体 | 三维矢量用 `\bm{A}` 或 `\vect{A}`，四维矢量用上标 `A^\mu` |
| 标量斜体 | 标量用斜体 `$A$`，单位用正体 `\mathrm{m}` |
| 偏导数 | 统一使用 `\partial_t f` 或 `\partial f/\partial t`，不可混用 |
| 重复指标 | 爱因斯坦求和约定仅在第 10 章及附录中启用，正文需显式写出求和号 |
| 量纲校验 | **每道计算题末尾必须附量纲校验**，格式：`[M] = ... ✓` |

### 1.2 核心公式编号

以下公式必须使用 `equation` 环境并添加 `\label`：

- 麦克斯韦四方程（高斯、无磁单极、法拉第、安培-麦克斯韦）
- 泊松方程、拉普拉斯方程
- 达朗贝尔方程（标势 + 矢势）
- 洛伦兹力公式

其他推导过程中的中间步骤使用 `\[` `\]` 或 `align*`。

### 1.3 术语一致性

| 术语 | 正确写法 | 禁用写法 |
|------|----------|----------|
| 叉积 | 叉积 | 又积 |
| 电介质 | 电介质 | 介质（单独使用时） |
| 磁化强度 | 磁化强度 $\vect{M}$ | 磁矩密度 |
| 库仑规范 | 库仑规范 | Coulomb gauge（正文用中文） |
| 洛伦兹规范 | 洛伦兹规范 | Lorentz gauge（正文用中文） |

---

## 二、排版规范

### 2.1 环境使用

```latex
% 定理/定义/推论（带编号）
\begin{theorem}{标题}{label}
\begin{definition}{标题}{label}
\begin{corollary}{标题}{label}

% 例题（带编号）
\begin{example}{标题}{label}
\difficulty{基础}  % 或 提高/挑战

% 物理洞见/常见误区/物理史话（带编号）
\begin{insight}{标题}{label}
\begin{warning}{标题}{label}
\begin{history}{标题}{label}

% 学习提示/本节要点（带编号）
\begin{tip}{标题}{label}
\begin{review}{标题}{label}

% 随堂自测（无编号）
\begin{miniquiz}

% 本章要点回顾（无编号）
\begin{chapterreview}
```

### 2.2 章节结构

```
\chapter{章标题}
\epigraph{名言}{--- 作者}  % 每章开篇引用
\begin{insight}{本章核心目标}{label}
  % 学习路径建议（必学/重要/可延后）
\end{insight}

\section{节标题}
\subsection{小节标题}

\begin{theorem}{定理名}{label}
  % 定理内容
\end{theorem}

\begin{example}{例题名}{label}
\difficulty{基础}
  % 题目描述
\tcblower
\textbf{解答：}
  % 分步解答
\end{example}

\begin{insight}{物理洞见}{label}
  % 深入理解
\end{insight}

\begin{warning}{常见误区}{label}
  % 学生易错点
\end{warning}

% 节末：本节要点
\begin{review}{本节要点}{label}
\end{review}

% 章末：随堂自测 + 本章要点回顾
\begin{miniquiz}
\end{miniquiz}

\begin{chapterreview}
\end{chapterreview}
```

### 2.3 图示规范

| 元素 | 颜色约定 |
|------|----------|
| 电场 $\vect{E}$ | 红色 `red` |
| 磁场 $\vect{B}$ | 蓝色 `blue` |
| 传播方向 $\vect{k}$ | 绿色 `green!50!black` |
| 力/电流 | 橙色 `cororange` |
| 等势面/波前 | 灰色/浅蓝 `blue!30` |

所有插图使用 TikZ 纯矢量绘制，禁止插入位图。

---

## 三、内容规范

### 3.1 新增内容要求

- **新增例题**：必须标注难度 `[基础]`/`[提高]`/`[挑战]`，末尾附量纲校验
- **新增定理**：必须给出证明或至少思路说明
- **新增洞见**：必须联系物理图像或实际应用
- **新增误区**：必须基于真实学生错误，给出正确做法

### 3.2 修改流程

1. **定位**：找到需要修改的章节和具体位置
2. **备份**：修改前记录原内容（复制到 CHANGELOG）
3. **修改**：按本规范执行
4. **校验**：
   - 物理公式量纲正确
   - 交叉引用可用 `\eqref{label}` 正常跳转
   - 编译零错误
5. **记录**：在 CHANGELOG.md 中登记修改

### 3.3 禁止事项

- ❌ 在表格内使用 `\begin{equation}` 环境
- ❌ 嵌套数学环境（如 `\[` 内再套 `\begin{equation}`）
- ❌ 混用 `$...$` 和 `\(...\)`（统一用 `$`）
- ❌ 公式编号遗漏或重复
- ❌ 未标注难度的例题
- ❌ 无物理意义的"纯数学"例题

---

## 四、编译检查清单

修改后必须执行：

```bash
xelatex -interaction=nonstopmode electrodynamics_textbook_v2.tex
xelatex -interaction=nonstopmode electrodynamics_textbook_v2.tex  # 第二次确保引用正确
```

**通过标准**：
- 零 `Error`
- 零 `! ` 开头致命错误
- `Output written on ...` 正常输出

---

*最后更新：2025-07-05*
