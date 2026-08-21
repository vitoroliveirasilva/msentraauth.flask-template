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
        throw "Command failed with exit code ${LASTEXITCODE}: $FilePath"
    }
}

$repositoryRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$outputRoot = Join-Path $repositoryRoot ".template-test-output"
$temporaryRoot = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd([IO.Path]::DirectorySeparatorChar)
$sourceSnapshot = Join-Path $temporaryRoot ("msentraauth-template-source-" + [guid]::NewGuid().ToString("N"))
$temporaryPrefix = $temporaryRoot + [IO.Path]::DirectorySeparatorChar
if (-not $sourceSnapshot.StartsWith($temporaryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to create source snapshot outside the temporary directory"
}

if (Test-Path -LiteralPath $outputRoot) {
    $resolvedOutput = (Resolve-Path -LiteralPath $outputRoot).Path
    if (-not $resolvedOutput.StartsWith($repositoryRoot + [IO.Path]::DirectorySeparatorChar)) {
        throw "Refusing to remove output outside the repository"
    }
    Remove-Item -LiteralPath $resolvedOutput -Recurse -Force
}
New-Item -ItemType Directory -Path $outputRoot | Out-Null
New-Item -ItemType Directory -Path $sourceSnapshot | Out-Null
Copy-Item -LiteralPath (Join-Path $repositoryRoot "copier.yml") -Destination $sourceSnapshot
Copy-Item -LiteralPath (Join-Path $repositoryRoot "template") -Destination $sourceSnapshot -Recurse

Push-Location $repositoryRoot
try {
    Invoke-NativeCommand "python" @(
        "-m", "pip", "install",
        "--constraint", "requirements/generator.constraints.txt",
        "copier", "jinja2", "mypy", "pytest", "pyyaml", "ruff"
    )
    Invoke-NativeCommand "ruff" @("check", "template_tests", "scripts/check_generated_project.py")
    Invoke-NativeCommand "mypy" @("template_tests", "scripts/check_generated_project.py")
    Invoke-NativeCommand "pytest" @("-q")

    $variants = @(
        @{ Name = "minimal"; Project = "Acme Portal"; Slug = "acme-portal"; Package = "acme_portal"; Graph = "false" },
        @{ Name = "graph"; Project = "Graph App"; Slug = "graph-app"; Package = "graph_core"; Graph = "true" }
    )
    foreach ($variant in $variants) {
        $destination = Join-Path $outputRoot $variant.Name
        Invoke-NativeCommand "copier" @(
            "copy", "--trust", "--defaults",
            "--data", "project_name=$($variant.Project)",
            "--data", "project_slug=$($variant.Slug)",
            "--data", "package_name=$($variant.Package)",
            "--data", "include_graph_example=$($variant.Graph)",
            "--data", "python_version=3.12",
            $sourceSnapshot, $destination
        )
        Invoke-NativeCommand "python" @("scripts/check_generated_project.py", $destination)
        Invoke-NativeCommand "python" @("-m", "compileall", "-q", (Join-Path $destination "src"), (Join-Path $destination "tests"))
    }
}
finally {
    Pop-Location
    if (Test-Path -LiteralPath $sourceSnapshot) {
        $resolvedSnapshot = (Resolve-Path -LiteralPath $sourceSnapshot).Path
        if (-not $resolvedSnapshot.StartsWith($temporaryPrefix, [StringComparison]::OrdinalIgnoreCase)) {
            throw "Refusing to remove source snapshot outside the temporary directory"
        }
        Remove-Item -LiteralPath $resolvedSnapshot -Recurse -Force
    }
}
