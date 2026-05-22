# 课程项目报告草稿

## 题目

基于变异测试反馈的大语言模型增强 EvoSuite 单元测试生成方法

英文题目：Mutation-Guided LLM Enhancement for EvoSuite-Generated Unit Tests

## 摘要

自动化单元测试生成能够降低测试编写成本。EvoSuite 作为搜索式测试生成工具，能够生成覆盖率较高的 JUnit 测试，但其测试 oracle 多为回归式断言，可读性和缺陷检测能力仍有提升空间。大语言模型具备代码语义理解能力，但直接生成测试容易出现编译错误、依赖幻觉和不稳定测试。本文实现一种混合式方法：先使用 EvoSuite 生成初始测试套件，再利用大语言模型根据源码、原始测试、覆盖率信息和 PIT survived mutants 生成增强测试，并通过 Maven 编译运行与修复循环保证测试可执行。实验对象为一个订单结算场景，包含会员折扣、优惠券、免运费、税费和金额边界等业务规则；评价指标包括 line coverage、branch coverage、mutation score、断言数量、可读性指标和 flaky rate。

## 1. 背景与问题

EvoSuite 的优化目标主要面向覆盖率，能够快速探索输入空间。但覆盖率不能完全衡量测试质量：测试执行了某行代码，不代表它能够发现该处的错误。Mutation testing 能通过人为注入小错误衡量测试 suite 的缺陷检测能力，因此更适合作为 oracle 强度的评价指标。

## 2. 方法

本文方法包括六个阶段：

1. EvoSuite 生成 seed JUnit 测试。
2. Maven 执行编译与测试，过滤无法运行的测试。
3. JaCoCo 与 PIT 产生覆盖率和变异测试报告。
4. 对 PIT survived mutants 做变异算子类型分类，并生成类型感知提示。
5. 从源码中抽取业务规则，作为 LLM 生成语义 oracle 的依据。
6. LLM 生成增强测试，若失败则进入 repair loop。

## 3. 实验对象

为了比简单工具类更能体现 LLM 的语义增强能力，本文使用一个小型订单结算系统作为实验对象。主要类包括：

| 类 | 作用 |
| --- | --- |
| `CheckoutCalculator` | 计算订单小计、会员折扣、优惠券折扣、运费、税费和最终金额 |
| `CouponPolicy` | 判断优惠券是否可用，并计算优惠金额 |
| `OrderItem` | 表示订单商品项 |
| `CustomerProfile` | 表示客户等级、积分、地区和是否首单 |
| `Coupon` | 表示优惠券类型、金额、门槛、过期时间和叠加规则 |
| `CheckoutRequest` | 表示一次结算请求 |
| `CheckoutResult` | 表示一次结算结果 |

该对象包含过期优惠券、首单优惠、高比例折扣限制、会员折扣封顶、非叠加优惠选择、数字商品免运费、VIP 免运费、地区税率等规则。它更容易产生“覆盖到了但断言不够强”的测试场景。

## 4. 实现

项目实现为外部编排框架，而不是修改 EvoSuite 内核。核心代码位于 `mglet/`。这种实现方式便于复现实验，也方便替换目标 Java 项目、LLM 模型或 EvoSuite jar。

## 5. 实验设计

对比组：

| 组别 | 说明 |
| --- | --- |
| Baseline 1 | EvoSuite 原始测试 |
| Baseline 2 | 纯 LLM 从零生成测试，可选 |
| Your Method | EvoSuite seed + LLM enhancement |
| Optional | ChatUniTest 默认方法，可选 |

主要指标：

| 指标 | 说明 |
| --- | --- |
| Compilation rate | 生成测试是否可编译 |
| Test pass rate | 测试是否稳定通过 |
| Line coverage | 行覆盖率 |
| Branch coverage | 分支覆盖率 |
| Mutation score | 缺陷检测能力 |
| Number of assertions | 断言数量 |
| Assertion strength score | 测试 oracle 强度 |
| Readability score | 可读性启发式分数 |
| Flaky failures | 多次运行失败次数 |

## 6. 创新点

本文实现三个可量化创新点：

| 创新点 | 说明 |
| --- | --- |
| 变异算子类型感知的 prompt | 根据 PIT survived mutants 的 mutator 类型，为边界、分支、数学公式、返回值等不同问题生成不同提示策略 |
| 业务规则增强的测试 oracle 生成 | 先从源码中抽取业务规则，再要求 LLM 将业务规则转化为语义断言 |
| Assertion Strength Score | 不只统计断言数量，还根据断言精确性、业务字段覆盖、金额断言和弱断言比例计算 oracle 强度 |

## 7. 预期结果分析

如果 LLM 只美化测试而不增强 oracle，line / branch coverage 可能变化不大，mutation score 也不会明显提升。若 LLM 成功针对 survived mutants 补充边界输入和语义断言，mutation score 应提升，survived mutants 数量应下降。订单结算场景中，优惠券、会员折扣和运费规则具有较强业务语义，因此比简单数学或字符串工具类更适合展示 LLM 的价值。

## 8. 局限性

- LLM 输出受模型能力和 prompt 稳定性影响。
- PIT 运行成本高，类数量过多时实验时间较长。
- 静态可读性指标只是近似代理，仍建议加入少量人工评分。
- 本实现采用外部编排方式，没有修改 EvoSuite 遗传算法内核。

## 9. 结论

本项目验证了一种实用的混合式测试生成路线：EvoSuite 提供可运行 seed，LLM 根据 mutation feedback 提升 oracle 和边界测试，Maven/PIT/JaCoCo 提供自动验证与量化评价。相比单纯覆盖率驱动，该方法更能体现测试缺陷检测能力。
