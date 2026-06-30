<#
.SYNOPSIS
  Helper script for Alembic migrations on Windows.
.EXAMPLE
  .\migrate.ps1 new "add field telefono to cliente"
  .\migrate.ps1 up
  .\migrate.ps1 down
  .\migrate.ps1 current
  .\migrate.ps1 history
#>

param(
    [Parameter(Position = 0)]
    [ValidateSet('new', 'up', 'down', 'current', 'history')]
    [string]$Command = 'up',

    [Parameter(Position = 1)]
    [string]$Message = ''
)

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
Push-Location $root
try {
    switch ($Command) {
        'new' {
            if (-not $Message) { $Message = Read-Host "Migration description" }
            python -m alembic revision --autogenerate -m "$Message"
        }
        'up'   { python -m alembic upgrade head }
        'down' { python -m alembic downgrade -1 }
        'current' { python -m alembic current }
        'history' { python -m alembic history }
    }
} finally {
    Pop-Location
}
