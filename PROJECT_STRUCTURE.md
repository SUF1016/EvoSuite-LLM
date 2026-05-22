# 项目结构说明

本文档说明当前目录中每个文件夹存放什么类型的文件，以及主要文件的作用。

## 根目录

| 文件/文件夹 | 作用 |
| --- | --- |
| `README.md` | 项目总说明，包含项目目标、运行方式、创新点和实验流程。 |
| `PROJECT_STRUCTURE.md` | 当前结构说明文档。 |
| `pyproject.toml` | Python 项目配置，声明包名、Python 版本和命令行入口。 |
| `.gitignore` | 忽略 Python 缓存、Maven target、实验输出等可再生成文件。 |
| `configs/` | 实验配置文件目录。 |
| `docs/` | 设计说明、实验指南和课程报告草稿。 |
| `java-target/` | Java 实验对象项目，已从原来的 `examples/java-target` 上移到根目录以减少嵌套。 |
| `mglet/` | 本项目的 Python 核心实现。 |
| `runs/` | 实验运行输出目录，保存每次运行的结果、日志、LLM 响应和摘要。 |
| `scripts/` | PowerShell 运行脚本。 |
| `tests/` | Python 框架自身的单元测试。 |
| `tools/` | 外部运行工具，包括 EvoSuite jar 和本地 Maven。 |

## `configs/`

| 文件 | 作用 |
| --- | --- |
| `course-project.json` | 正式实验配置。指定 Java 项目路径、目标类、EvoSuite 参数、Maven 命令、Qwen/DashScope API 配置和 prompt 限制。 |
| `smoke-test.json` | 冒烟测试配置。使用相同 Java 目标，但 `llm.dry_run=true`，用于验证 EvoSuite/Maven/PIT/JaCoCo 链路，不真实生成 LLM 增强测试。 |

## `docs/`

| 文件 | 作用 |
| --- | --- |
| `DESIGN.md` | 系统设计说明，解释 EvoSuite、LLM、PIT、JaCoCo 和三个创新点如何协作。 |
| `EXPERIMENT_GUIDE.md` | 实验指南，说明实验对象、指标含义、输出文件和常见问题。 |
| `COURSE_REPORT_DRAFT.md` | 课程报告草稿，包含题目、摘要、方法、实验设计、创新点和局限性。 |

## `java-target/`

这是当前实验对象，一个小型 Java Maven 订单结算项目。

| 文件/文件夹 | 作用 |
| --- | --- |
| `pom.xml` | Maven 配置。声明 JUnit、EvoSuite runtime、JaCoCo、PIT 等依赖和插件。 |
| `src/main/java/` | Java 生产代码，即 EvoSuite 和 LLM 要生成测试的目标代码。 |
| `src/test/java/` | 测试代码目录。当前包含 EvoSuite 生成的 seed tests；正式运行时也会被写入 LLM 增强测试。 |

### `java-target/src/main/java/order/`

| 文件 | 作用 |
| --- | --- |
| `CheckoutCalculator.java` | 订单结算核心类。计算小计、会员折扣、优惠券折扣、运费、税费和最终金额。 |
| `CouponPolicy.java` | 优惠券策略类。判断优惠券是否可用，并计算优惠金额。 |
| `Coupon.java` | 优惠券实体。包含优惠券类型、金额、使用门槛、过期时间、首单限制和是否可叠加。 |
| `CouponType.java` | 优惠券类型枚举：百分比、固定金额、免运费。 |
| `CustomerProfile.java` | 客户信息。包含会员等级、积分、是否首单和地区。 |
| `CustomerTier.java` | 客户等级枚举：游客、会员、VIP。 |
| `OrderItem.java` | 订单商品项。包含 SKU、数量、单价、是否数字商品和品类。 |
| `CheckoutRequest.java` | 一次结算请求。组合商品、客户、优惠券和是否加急配送。 |
| `CheckoutResult.java` | 一次结算结果。包含小计、折扣、运费、税费、总价、优惠券是否生效和提示信息。 |

### `java-target/src/test/java/order/`

| 文件 | 作用 |
| --- | --- |
| `CheckoutCalculator_ESTest.java` | EvoSuite 为 `CheckoutCalculator` 自动生成的 seed JUnit 测试。 |
| `CouponPolicy_ESTest.java` | EvoSuite 为 `CouponPolicy` 自动生成的 seed JUnit 测试。 |
| `CheckoutCalculatorLLMEnhancedTest.java` | 真实 API 实验第二轮生成并验证通过的 `CheckoutCalculator` 增强测试。 |
| `CouponPolicyLLMEnhancedTest.java` | 真实 API 实验第二轮生成并验证通过的 `CouponPolicy` 增强测试。 |

这些 `_ESTest.java` 文件可删除并重新生成。完整 pipeline 会重新调用 EvoSuite 生成 seed tests。

## `mglet/`

这是项目的核心 Python 实现。

| 文件 | 作用 |
| --- | --- |
| `__init__.py` | Python 包初始化文件，声明版本信息。 |
| `__main__.py` | 支持使用 `python -m mglet` 启动命令行。 |
| `cli.py` | 命令行入口。支持 `run`、`evaluate`、`print-config`、`render-report` 等命令，并隐藏 API key。 |
| `command.py` | 统一执行外部命令，记录参数、工作目录、stdout、stderr、退出码和耗时。 |
| `config.py` | 读取 JSON 配置、合并默认配置、展开环境变量、解析路径。 |
| `java_project.py` | Maven Java 项目辅助函数。负责定位源码/测试、运行 Maven goal、构建 classpath、导出 EvoSuite 测试。 |
| `evosuite.py` | EvoSuite Runner。调用 `tools/evosuite-1.2.0.jar` 生成 JUnit seed tests。 |
| `coverage.py` | JaCoCo 解析器。读取 `target/site/jacoco/jacoco.xml` 并提取覆盖率指标。 |
| `pitest.py` | PIT 解析器。读取 `mutations.xml`、计算 mutation score、提取 survived mutants，并实现变异算子类型分类。 |
| `prompting.py` | Prompt 构造模块。负责业务规则抽取 prompt、变异算子类型感知 prompt、增强测试 prompt 和修复 prompt。 |
| `llm.py` | OpenAI-compatible LLM 客户端。当前配置为阿里云 DashScope Qwen，也支持 dry-run 和文件响应。 |
| `patching.py` | LLM 输出解析器。从 fenced Java code block 中提取文件路径和代码，并安全写入项目目录。 |
| `static_metrics.py` | 静态测试指标计算。统计测试数、断言数、可读性、test smell 和 Assertion Strength Score。 |
| `evaluator.py` | 评估器。运行 Maven test、JaCoCo、PIT，并汇总覆盖率、mutation score 和静态指标。 |
| `reports.py` | 报告生成器。输出 `results.json` 和 `summary.md`。 |
| `pipeline.py` | 主流程编排器。串联 EvoSuite 生成、业务规则抽取、LLM 增强、验证修复、PIT/JaCoCo 评估。 |
| `models.py` | 数据模型。定义命令结果、PIT 报告、覆盖率报告、静态指标和评估结果等结构。 |

## `scripts/`

| 文件 | 作用 |
| --- | --- |
| `run_demo.ps1` | 正式运行脚本。设置 JDK/Maven 环境，读取 DashScope 环境变量，把中文项目路径临时映射到 `M:`，然后运行完整 pipeline。 |
| `smoke_python.ps1` | Python 冒烟测试脚本。验证 Python 编译、单元测试和配置解析。 |
| `fill_project_report.py` | 基于 `26项目报告.docx` 模板生成 `26项目报告_已填写.docx` 的报告填写脚本。 |

## `tests/`

这些是 Python 框架自身的测试，不是 Java 业务项目的测试。

| 文件 | 作用 |
| --- | --- |
| `__init__.py` | 让 `tests` 成为 Python 测试包。 |
| `test_metrics_parsers.py` | 测试 JaCoCo/PIT 解析、变异算子分类和静态指标计算。 |
| `test_patching.py` | 测试 LLM 返回的 Java code block 能否被正确提取成文件。 |
| `test_reports.py` | 测试 Markdown 实验摘要表格生成。 |

## `tools/`

| 文件/文件夹 | 作用 |
| --- | --- |
| `evosuite-1.2.0.jar` | EvoSuite 官方 release jar。实际用于生成 JUnit 测试，不是从 `evosuite-master` 提取的。 |
| `apache-maven-3.9.16/` | 本地 Maven 发行版。脚本用它执行 `mvn test`、JaCoCo 和 PIT。 |
| `README.md` | 工具目录说明。 |

### `tools/apache-maven-3.9.16/`

这是 Apache Maven 官方二进制发行目录，属于外部工具，不是本项目手写源码。

| 文件/文件夹 | 作用 |
| --- | --- |
| `bin/` | Maven 启动脚本，例如 `mvn.cmd`。 |
| `boot/` | Maven 启动所需的 classworlds 引导 jar。 |
| `conf/` | Maven 默认配置文件，例如 `settings.xml`。 |
| `lib/` | Maven 自带依赖 jar。 |
| `LICENSE` | Maven 许可证。 |
| `NOTICE` | Maven 第三方声明。 |
| `README.txt` | Maven 官方说明。 |

## 运行后会重新出现的生成目录

以下目录被 `.gitignore` 忽略，可删除，可重新生成：

| 目录 | 作用 |
| --- | --- |
| `runs/` | 每次 pipeline 的实验结果，包括 `summary.md`、`results.json`、命令日志和 LLM 响应。 |
| `java-target/target/` | Maven 编译结果、JaCoCo 报告、PIT 报告和测试运行报告。 |
| `java-target/evosuite-tests/` | EvoSuite 原始生成测试输出。 |
| `java-target/evosuite-report/` | EvoSuite 生成统计报告。 |
| `__pycache__/` | Python 缓存目录。 |