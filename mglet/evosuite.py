from __future__ import annotations

from pathlib import Path

from .command import CommandError, run_command, write_command_log
from .java_project import build_maven_classpath, export_evosuite_tests, run_maven_goal


class EvoSuiteRunner:
    def __init__(self, project_dir: Path, config: dict, output_dir: Path) -> None:
        self.project_dir = project_dir
        self.config = config
        self.output_dir = output_dir

    def generate(self, target_class: str) -> list[Path]:
        maven_cfg = self.config["maven"]
        evosuite_cfg = self.config["evosuite"]
        java_executable = self.config["java"].get("executable", "java")
        evosuite_jar = (Path(evosuite_cfg["jar"]) if evosuite_cfg.get("jar") else Path()).resolve()
        if not evosuite_jar.exists():
            raise FileNotFoundError(
                "EvoSuite jar not found. Build the local EvoSuite source or download "
                f"a release jar, then set evosuite.jar in config. Current value: {evosuite_jar}"
            )

        compile_result = run_maven_goal(self.project_dir, maven_cfg, "compile_goal")
        write_command_log(compile_result, self.output_dir / "commands", "maven_compile")
        if not compile_result.ok:
            raise CommandError("Maven test-compile failed before EvoSuite generation", compile_result)

        cp_file = self.output_dir / "maven-classpath.txt"
        project_cp = build_maven_classpath(
            self.project_dir,
            maven_cfg.get("executable", "mvn"),
            int(maven_cfg.get("timeout_seconds", 900)),
            cp_file,
        )

        args = [
            java_executable,
            "-jar",
            str(evosuite_jar),
            "-class",
            target_class,
            "-projectCP",
            project_cp,
            f"-Dtest_dir={evosuite_cfg.get('test_dir', 'evosuite-tests')}",
            f"-Dreport_dir={evosuite_cfg.get('report_dir', 'evosuite-report')}",
            f"-Dsearch_budget={int(evosuite_cfg.get('search_budget_seconds', 60))}",
        ]
        args.extend(str(a) for a in evosuite_cfg.get("extra_args", []))
        result = run_command(
            args,
            cwd=self.project_dir,
            timeout_seconds=int(evosuite_cfg.get("timeout_seconds", 1800)),
        )
        write_command_log(
            result,
            self.output_dir / "commands",
            f"evosuite_{target_class.replace('.', '_')}",
        )
        if not result.ok:
            raise CommandError("EvoSuite generation failed", result)

        if evosuite_cfg.get("export_to_test_tree", True):
            return export_evosuite_tests(self.project_dir, evosuite_cfg.get("test_dir", "evosuite-tests"))
        return []
