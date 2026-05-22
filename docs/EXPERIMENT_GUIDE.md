# 实验指南

## 实验对象

默认样例项目在 `java-target`，现在使用一个小型订单结算场景。核心可测类是：

- `order.CheckoutCalculator`
- `order.CouponPolicy`

该场景包含会员等级、优惠券、满减/折扣、免运费、税费、金额封顶、过期校验和异常分支。相比简单工具类，它更适合展示 LLM 根据业务语义补充测试 oracle 的价值。

## 为什么这个对象更适合展示改进

EvoSuite 擅长探索输入并提升覆盖率，但它不真正理解业务规则。例如：

- VIP 普通配送应免运费。
- 过期优惠券不应生效。
- 非叠加优惠券只应保留更优折扣。
- 高比例优惠券只允许 VIP 使用。
- 折扣不能超过订单小计的上限。
- 数字商品不应产生运费。

这些规则即使被测试执行到，断言也可能只是回归式的当前行为断言。LLM 更容易根据类名、方法名和源码语义补出可解释的断言，因此 mutation score 和 survived mutant 数量更能体现差异。

## 推荐实验步骤

1. Baseline 1：EvoSuite 原始测试
   - 运行完整 pipeline 后读取 `evosuite-baseline` 行。
   - 记录 line coverage、branch coverage、mutation score、assertion count。

2. Your Method：EvoSuite seed + LLM enhancement
   - 读取 `llm-iteration-1` 和 `llm-iteration-2`。
   - 重点比较 mutation score 是否提升、survived mutants 是否下降。

3. Flaky 检查
   - 配置中 `flaky_runs` 默认为 3。
   - 如果 `flaky_failures > 0`，说明生成测试存在不稳定行为。

## 可量化指标

| 指标 | 来源 | 解释 |
| --- | --- | --- |
| Compilation / test pass | `mvn test` | 测试是否可编译并稳定运行 |
| Line coverage | JaCoCo | 被执行的代码行比例 |
| Branch coverage | JaCoCo | 被执行的分支比例 |
| Mutation score | PIT | 被测试杀死的有效变异体比例 |
| Number of assertions | 静态扫描 | oracle 强度的粗略代理 |
| Assertion strength | 静态扫描 | 精确金额断言、业务字段断言、异常断言等组成的 oracle 强度分数 |
| Readability score | 静态启发式 | 方法名、test smell 的综合得分 |
| Flaky failures | 多次 `mvn test` | 测试稳定性 |

## 输出文件解释

每次运行会生成一个时间戳目录：

```text
runs/course-project/20260521-xxxxxx/
```

其中：

- `results.json`：所有指标的机器可读结果。
- `summary.md`：可复制到课程报告的对比表。
- `commands/*.json`：每条 Maven/EvoSuite 命令的 stdout/stderr 和耗时。
- `llm/*.md`：每一轮 LLM 原始响应，便于复现实验。
- `pom.xml.snapshot`：实验开始时的 Maven 配置快照。

## 常见问题

### 找不到 java 或 mvn

安装 JDK 和 Maven，并确认：

```powershell
java -version
mvn -version
```

本项目脚本默认使用已安装的 JDK 8 和 `tools/apache-maven-3.9.16`。

### 找不到 EvoSuite jar

默认配置读取：

```text
tools/evosuite-1.2.0.jar
```

### 中文路径导致 JaCoCo 报告为空

请使用脚本运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

脚本会把项目临时映射到 `M:` 盘符，避免 JaCoCo agent 使用中文绝对路径时写不出 `jacoco.exec`。
