# MGLET 使用说明

MGLET 是本课程项目的实验框架，全名为 **Mutation-Guided LLM Enhancement for EvoSuite-Generated Unit Tests**。它的作用是：

```text
Java Maven 项目
  -> EvoSuite 生成 JUnit seed tests
  -> Maven/JUnit 验证
  -> JaCoCo 统计覆盖率
  -> PIT 统计 mutation score 和 survived mutants
  -> LLM 根据业务规则和变异测试反馈增强测试
  -> 验证、修复、再次评估
  -> 输出 results.json、summary.md 和课程报告
```

当前默认实验对象是 [java-target](java-target)，目标类为：

```text
order.CheckoutCalculator
order.CouponPolicy
```

## 1. 目录说明

| 路径 | 用途 |
| --- | --- |
| `mglet/` | Python 实验框架源码，负责调用 EvoSuite、Maven、PIT、JaCoCo 和 LLM。 |
| `java-target/` | Java Maven 实验对象，订单结算业务场景。 |
| `configs/` | 实验配置文件。 |
| `scripts/` | 常用 PowerShell 脚本。 |
| `tests/` | Python 框架自身的单元测试。 |
| `tools/` | 本地工具目录，包含 EvoSuite jar 和 Maven。 |
| `runs/` | 每次实验的输出目录。 |
| `docs/` | 设计说明、实验指南和报告草稿。 |
| `PROJECT_STRUCTURE.md` | 更详细的文件夹和文件作用说明。 |
| `26项目报告_已填写.docx` | 根据真实实验结果填写后的课程报告。 |

## 2. 环境要求

本项目当前已经配置为使用：

- Python 3.10+
- Temurin JDK 8
- `tools/apache-maven-3.9.16`
- `tools/evosuite-1.2.0.jar`
- 阿里云 DashScope OpenAI-compatible 接口
- 默认模型：`qwen3.6-plus`

EvoSuite 1.2.0 在 JDK 17 下容易遇到 Java module 反射限制，所以这里默认使用 JDK 8。

## 3. 配置 API Key

在 PowerShell 中设置环境变量：

```powershell
$env:DASHSCOPE_API_KEY="你的 API Key"
$env:OPENAI_BASE_URL="https://dashscope.aliyuncs.com/compatible-mode/v1"
$env:OPENAI_MODEL="qwen3.6-plus"
```

如果你已经把这些变量写入了 Windows 用户环境变量，可以直接运行脚本，`scripts/run_demo.ps1` 会自动读取。

配置文件位置：

```text
configs/course-project.json
configs/smoke-test.json
```

其中 `course-project.json` 用于真实实验，`smoke-test.json` 用于快速检查流程。

## 4. 快速检查项目是否能运行

先运行 Python 框架单元测试：

```powershell
python -m unittest discover -v
```

检查配置是否能被正确读取：

```powershell
python -m mglet --config configs/course-project.json print-config --pretty
```

如果只想做轻量冒烟测试：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\smoke_python.ps1
```

## 5. 运行完整实验

推荐使用脚本运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

脚本会做这些事：

1. 设置 JDK 8 和 Maven 路径。
2. 读取 DashScope / OpenAI-compatible API 环境变量。
3. 把当前中文路径临时映射为 `M:` 盘。
4. 调用 `python -m mglet --config configs/course-project.json run`。
5. 生成新的实验目录，例如 `runs/course-project/20260521-213542`。

使用 `M:` 是为了避免部分 Java 工具在中文绝对路径下写 JaCoCo/PIT 产物失败。

## 6. 跳过 EvoSuite，复用已有 seed tests

如果 `java-target/src/test/java/order/` 中已经有 EvoSuite 生成的 `_ESTest.java`，可以跳过 EvoSuite，直接进行 LLM 增强和评估：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1 -SkipEvoSuite
```

这适合反复调 prompt 或调 LLM 参数时使用，可以节省 EvoSuite 生成时间。

## 7. 只评估当前测试套件

如果你只想评估当前 `java-target/src/test/java/order/` 里的测试，不调用 EvoSuite，也不调用 LLM：

```powershell
python -m mglet --config configs/course-project.json evaluate --label manual
```

这个命令会运行：

- `mvn test`
- JaCoCo
- PIT
- 静态测试指标统计

输出同样会进入 `runs/course-project/<run-id>/`。

## 8. 查看实验结果

每次完整实验会生成一个目录：

```text
runs/course-project/<run-id>/
```

常用文件：

| 文件 | 作用 |
| --- | --- |
| `summary.md` | 最重要，直接给出 baseline 和 LLM iteration 的指标对比。 |
| `results.json` | 完整结构化结果，包含 coverage、mutation、静态指标和命令日志。 |
| `commands/*.json` | 每条 Maven/EvoSuite/PIT 命令的 stdout、stderr、耗时和退出码。 |
| `llm/*.md` | LLM 的业务规则抽取、测试生成和 repair 响应。 |
| `pom.xml.snapshot` | 实验开始时的 Maven 配置快照。 |

最近一次真实 API 实验结果在：

```text
runs/course-project/20260521-213542/summary.md
```

关键结果：

| 方法 | Test OK | Line Coverage | Branch Coverage | Mutation Score | Assertions | Assertion Strength |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| EvoSuite baseline | yes | 88.99% | 85.34% | 69.44% | 29 | 39.1 |
| LLM iteration 1 | no | 88.99% | 85.34% | 69.44% | 74 | 76.3 |
| LLM iteration 2 | yes | 92.20% | 85.34% | 94.44% | 64 | 68.0 |

结论：第二轮 LLM 增强测试通过验证，并将 mutation score 从 `69.44%` 提升到 `94.44%`。

## 9. 重新渲染已有结果

如果已有 `results.json`，只想重新生成 `summary.md`：

```powershell
python -m mglet --config configs/course-project.json render-report runs/course-project/<run-id>/results.json
```

示例：

```powershell
python -m mglet --config configs/course-project.json render-report runs/course-project/20260521-213542/results.json
```

## 10. 重要配置项

主要配置文件：[configs/course-project.json](configs/course-project.json)

常用字段：

| 字段 | 说明 |
| --- | --- |
| `project_dir` | Java Maven 项目路径，当前为 `java-target`。 |
| `output_dir` | 实验输出路径，当前为 `runs/course-project`。 |
| `targets` | 要生成和增强测试的 Java 类。 |
| `iterations` | LLM 增强迭代轮数。 |
| `repair_attempts` | LLM 生成测试失败后的修复次数。 |
| `flaky_runs` | 测试重复运行次数，用于发现不稳定测试。 |
| `evosuite.search_budget_seconds` | EvoSuite 每个目标类的搜索时间。 |
| `llm.model` | 使用的模型名，默认从 `OPENAI_MODEL` 读取。 |
| `llm.extra_body.enable_thinking` | 当前设置为 `false`，避免 Qwen thinking 模式导致非流式调用过慢。 |
| `prompt.max_mutants` | 每轮传给 LLM 的 survived mutants 数量上限。 |

## 11. 输出的测试文件在哪里

EvoSuite seed tests：

```text
java-target/src/test/java/order/CheckoutCalculator_ESTest.java
java-target/src/test/java/order/CouponPolicy_ESTest.java
```

LLM 增强测试：

```text
java-target/src/test/java/order/CheckoutCalculatorLLMEnhancedTest.java
java-target/src/test/java/order/CouponPolicyLLMEnhancedTest.java
```

这些测试文件会被 Maven、JaCoCo 和 PIT 一起使用。

## 12. 常见问题

**1. API 调用超时怎么办？**

优先确认 `configs/course-project.json` 中：

```json
"timeout_seconds": 300,
"retries": 3,
"extra_body": {
  "enable_thinking": false
}
```

长 prompt 下建议关闭 thinking，并限制 `prompt.max_mutants` 和 `prompt.max_test_chars`。

**2. Java 测试失败怎么办？**

先运行：

```powershell
python -m mglet --config configs/course-project.json evaluate --label manual
```

再查看：

```text
runs/course-project/<run-id>/commands/manual_maven_test.json
```

里面有 Maven 编译或 JUnit 失败日志。

**3. 想重新生成所有测试怎么办？**

可以删除这些生成目录或文件后重新运行完整实验：

```text
java-target/src/test/java/order/*_ESTest.java
java-target/src/test/java/order/*LLMEnhancedTest.java
java-target/target/
java-target/evosuite-tests/
java-target/evosuite-report/
runs/
```

然后运行：

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_demo.ps1
```

**4. 为什么重点看 mutation score，而不是只看 coverage？**

EvoSuite 本身就是 coverage-driven，覆盖率高并不代表断言强。Mutation score 会检查测试能否杀死人为注入的小缺陷，更能体现测试 oracle 是否有效。