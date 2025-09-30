param(
    [Parameter(Mandatory=$true)]
    [ValidateSet("install", "migrate", "run", "test")]
    [string]$Task
)

$env:PYTHONPATH = "$PSScriptRoot"
$python = Join-Path $PSScriptRoot ".venv\\Scripts\\python.exe"
if (!(Test-Path $python)) {
    Write-Error "Virtual environment missing. Run `py -3.11 -m venv .venv` first."
    exit 1
}

switch ($Task) {
    "install" {
        & $python -m pip install -r requirements.txt
    }
    "migrate" {
        & $python manage.py migrate
    }
    "run" {
        & $python manage.py runserver
    }
    "test" {
        & $python manage.py test
    }
}
