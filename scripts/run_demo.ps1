param(
    [string]$Config = "configs/course-project.json",
    [switch]$SkipEvoSuite
)

$ErrorActionPreference = "Stop"
$Jdk = "C:\Program Files\Eclipse Adoptium\jdk-8.0.492.9-hotspot"
$Maven = Join-Path (Resolve-Path ".\tools").Path "apache-maven-3.9.16"
$env:JAVA_HOME = $Jdk
$env:Path = "$Jdk\bin;$Maven\bin;$env:Path"
if (-not $env:DASHSCOPE_API_KEY) {
    $env:DASHSCOPE_API_KEY = [Environment]::GetEnvironmentVariable("DASHSCOPE_API_KEY", "User")
}
if (-not $env:OPENAI_BASE_URL) {
    $env:OPENAI_BASE_URL = [Environment]::GetEnvironmentVariable("OPENAI_BASE_URL", "User")
}
if (-not $env:OPENAI_MODEL) {
    $env:OPENAI_MODEL = [Environment]::GetEnvironmentVariable("OPENAI_MODEL", "User")
}

$ProjectRoot = (Resolve-Path ".").Path
$Drive = "M:"
$Existing = subst | Select-String "^$([regex]::Escape($Drive))\\:"
if (-not $Existing) {
    subst $Drive $ProjectRoot
}

try {
    Push-Location "$Drive\"
    $argsList = @("-m", "mglet", "--config", $Config, "run")
    if ($SkipEvoSuite) {
        $argsList += "--skip-evosuite"
    }
    python @argsList
}
finally {
    Pop-Location
}
