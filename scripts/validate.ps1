$ErrorActionPreference = "Stop"

function Invoke-NativeCommand {
    param(
        [Parameter(Mandatory = $true)]
        [string]$FilePath,

        [Parameter()]
        [string[]]$ArgumentList = @()
    )

    & $FilePath @ArgumentList
    if ($LASTEXITCODE -ne 0) {
        $renderedArguments = $ArgumentList -join " "
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath $renderedArguments"
    }
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Push-Location $repositoryRoot

try {
    Invoke-NativeCommand -FilePath "python" -ArgumentList @("-m", "pip", "install", "-e", ".[dev]")
    Invoke-NativeCommand -FilePath "ruff" -ArgumentList @("check", ".")
    Invoke-NativeCommand -FilePath "ruff" -ArgumentList @("format", "--check", ".")
    Invoke-NativeCommand -FilePath "mypy" -ArgumentList @("src", "tests")
    Invoke-NativeCommand -FilePath "python" -ArgumentList @("-m", "compileall", "-q", "src", "tests")
    Invoke-NativeCommand -FilePath "pytest"
    Invoke-NativeCommand -FilePath "bandit" -ArgumentList @("-c", "pyproject.toml", "-r", "src")
    Invoke-NativeCommand -FilePath "pip-audit" -ArgumentList @(".")
    Invoke-NativeCommand -FilePath "python" -ArgumentList @("-m", "pip", "check")

    Remove-Item -Recurse -Force dist, build -ErrorAction SilentlyContinue
    Invoke-NativeCommand -FilePath "python" -ArgumentList @("-m", "build")
    Invoke-NativeCommand -FilePath "python" -ArgumentList @("-m", "twine", "check", "dist/*")

    $env:DIST_DIR = "dist"
    try {
        Invoke-NativeCommand -FilePath "pytest" -ArgumentList @("tests/test_distribution.py", "--no-cov")
    }
    finally {
        Remove-Item Env:DIST_DIR -ErrorAction SilentlyContinue
    }
}
finally {
    Pop-Location
}
