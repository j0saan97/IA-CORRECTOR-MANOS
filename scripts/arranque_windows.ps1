# Instala (o quita) la tarea de Windows que arranca el watcher al iniciar sesión, sin ventana.
#   Instalar:     powershell -ExecutionPolicy Bypass -File scripts\arranque_windows.ps1
#   Quitar:       powershell -ExecutionPolicy Bypass -File scripts\arranque_windows.ps1 -Quitar
#   Ver estado:   Get-ScheduledTask -TaskName "IA-Corrector-Manos" | Get-ScheduledTaskInfo
param([switch]$Quitar)

$TaskName = "IA-Corrector-Manos"
$Proyecto = Split-Path -Parent $PSScriptRoot

if ($Quitar) {
    Unregister-ScheduledTask -TaskName $TaskName -Confirm:$false
    Write-Output "Tarea '$TaskName' eliminada."
    exit 0
}

$python = (Get-Command python -ErrorAction Stop).Source
$pythonw = Join-Path (Split-Path $python) "pythonw.exe"
if (-not (Test-Path $pythonw)) { throw "No se encuentra $pythonw" }

$action = New-ScheduledTaskAction -Execute $pythonw -Argument "`"$Proyecto\main.py`"" -WorkingDirectory $Proyecto
# 1 min de retraso tras iniciar sesión: da tiempo a que arranque PostgreSQL de PT4 y la red
$trigger = New-ScheduledTaskTrigger -AtLogOn -User $env:USERNAME
$trigger.Delay = "PT1M"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit ([TimeSpan]::Zero) `
    -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
    -MultipleInstances IgnoreNew `
    -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -StartWhenAvailable

Register-ScheduledTask -TaskName $TaskName -Action $action -Trigger $trigger -Settings $settings `
    -Description "Vigila Hand_Review y sube las manos a poker-library.com" -Force | Out-Null

Write-Output "Tarea '$TaskName' instalada: arranca $pythonw main.py al iniciar sesión (sin ventana)."
