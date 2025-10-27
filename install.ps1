#
# Docuchango Installer for Windows
# Install docuchango documentation validation framework using uv
#
# Usage:
#   irm https://raw.githubusercontent.com/jrepp/docuchango/main/install.ps1 | iex
#   Or locally: .\install.ps1
#

$ErrorActionPreference = "Stop"

# Configuration
$PYTHON_MIN_VERSION = "3.10"

function Print-Header {
    Write-Host ""
    Write-Host "╔════════════════════════════════════════╗" -ForegroundColor Blue
    Write-Host "║     Docuchango Installer v0.1.0      ║" -ForegroundColor Blue
    Write-Host "╚════════════════════════════════════════╝" -ForegroundColor Blue
    Write-Host ""
}

function Print-Step {
    param($Message)
    Write-Host "▸ $Message" -ForegroundColor Blue
}

function Print-Success {
    param($Message)
    Write-Host "✓ $Message" -ForegroundColor Green
}

function Print-Error {
    param($Message)
    Write-Host "✗ $Message" -ForegroundColor Red
}

function Print-Warning {
    param($Message)
    Write-Host "⚠ $Message" -ForegroundColor Yellow
}

function Check-Python {
    Print-Step "Checking Python installation..."

    $pythonCmd = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCmd) {
        $pythonCmd = Get-Command python3 -ErrorAction SilentlyContinue
    }

    if (-not $pythonCmd) {
        Print-Error "Python 3 is not installed"
        Write-Host "Please install Python $PYTHON_MIN_VERSION or higher from https://www.python.org/"
        exit 1
    }

    $pythonExe = $pythonCmd.Source
    $pythonVersion = & $pythonExe -c "import sys; print('.'.join(map(str, sys.version_info[:2])))"
    Print-Success "Found Python $pythonVersion"

    # Check version
    $requiredParts = $PYTHON_MIN_VERSION.Split('.')
    $currentParts = $pythonVersion.Split('.')

    $requiredMajor = [int]$requiredParts[0]
    $requiredMinor = [int]$requiredParts[1]
    $currentMajor = [int]$currentParts[0]
    $currentMinor = [int]$currentParts[1]

    if (($currentMajor -lt $requiredMajor) -or (($currentMajor -eq $requiredMajor) -and ($currentMinor -lt $requiredMinor))) {
        Print-Error "Python $PYTHON_MIN_VERSION or higher is required (found $pythonVersion)"
        exit 1
    }

    return $pythonExe
}

function Check-Uv {
    Print-Step "Checking for uv..."

    $uvCmd = Get-Command uv -ErrorAction SilentlyContinue
    if ($uvCmd) {
        $uvVersion = & uv --version 2>&1 | Select-String -Pattern "uv (\d+\.\d+\.\d+)" | ForEach-Object { $_.Matches.Groups[1].Value }
        Print-Success "Found uv $uvVersion"
        return $true
    }
    else {
        Print-Error "uv is not installed"
        Write-Host ""
        Write-Host "uv is required to install docuchango."
        Write-Host "To install uv, run:"
        Write-Host ""
        Write-Host "  irm https://astral.sh/uv/install.ps1 | iex"
        Write-Host ""
        Write-Host "Or visit: https://docs.astral.sh/uv/getting-started/installation/"
        exit 1
    }
}

function Install-Docuchango {
    Print-Step "Installing docuchango with uv..."

    if (Test-Path ".git") {
        # Local development install
        & uv pip install -e .
    }
    else {
        # Install from PyPI
        & uv pip install docuchango
    }

    if ($LASTEXITCODE -ne 0) {
        Print-Error "Installation failed"
        exit 1
    }

    Print-Success "docuchango installed successfully"
}

function Verify-Installation {
    Print-Step "Verifying installation..."

    $docuchangoCmd = Get-Command docuchango -ErrorAction SilentlyContinue
    if (-not $docuchangoCmd) {
        Print-Warning "docuchango command not found in PATH"
        Write-Host ""
        Write-Host "You may need to add Python's Scripts directory to your PATH."
        Write-Host "Common locations:"
        Write-Host "  - C:\Users\$env:USERNAME\AppData\Local\Programs\Python\Python3XX\Scripts"
        Write-Host "  - C:\Users\$env:USERNAME\AppData\Roaming\Python\Python3XX\Scripts"
        Write-Host ""
        Write-Host "To add to PATH, run PowerShell as Administrator:"
        Write-Host '  $env:PATH += ";C:\Path\To\Python\Scripts"'
        Write-Host '  [System.Environment]::SetEnvironmentVariable("PATH", $env:PATH, [System.EnvironmentVariableTarget]::User)'
        Write-Host ""
        return $false
    }

    # Test the command
    $version = & docuchango --version 2>&1
    Print-Success "docuchango is available: $version"

    # Test help command
    & docuchango --help | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Print-Success "docuchango commands are working"
    }
    else {
        Print-Warning "docuchango command exists but help failed"
        return $false
    }

    return $true
}

function Show-NextSteps {
    Write-Host ""
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host "  Installation Complete!" -ForegroundColor Green
    Write-Host "═══════════════════════════════════════════════" -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:"
    Write-Host ""
    Write-Host "1. View the bootstrap guide:"
    Write-Host "   docuchango bootstrap" -ForegroundColor Blue
    Write-Host ""
    Write-Host "2. View agent instructions:"
    Write-Host "   docuchango bootstrap --guide agent" -ForegroundColor Blue
    Write-Host ""
    Write-Host "3. Validate your documentation:"
    Write-Host "   cd your-project" -ForegroundColor Blue
    Write-Host "   docuchango validate" -ForegroundColor Blue
    Write-Host ""
    Write-Host "4. Get help:"
    Write-Host "   docuchango --help" -ForegroundColor Blue
    Write-Host ""
    Write-Host "For more information, visit:"
    Write-Host "  https://github.com/jrepp/docuchango"
    Write-Host ""
}

function Main {
    Print-Header

    $pythonExe = Check-Python
    Check-Uv

    Write-Host ""
    Install-Docuchango

    Write-Host ""
    $verified = Verify-Installation

    if ($verified) {
        Show-NextSteps
    }
    else {
        Write-Host ""
        Print-Warning "Installation completed but verification had issues"
        Write-Host "Try running: docuchango --version"
        Write-Host ""
        Write-Host "If the command is not found, you may need to:"
        Write-Host "1. Restart your PowerShell"
        Write-Host "2. Add Python's bin directory to your PATH"
        Write-Host ""
    }
}

# Run main installation
Main
