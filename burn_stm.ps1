param(
    [string]$FilePath
)

$cli = "C:\ST\STM32CubeCLT_1.18.0\STM32CubeProgrammer\bin\STM32_Programmer_CLI.exe"

if (-not (Test-Path $cli)) {
    Write-Error "STM32CubeProgrammer CLI not found at $cli"
    exit 1
}

if (-not $FilePath) {
    Add-Type -AssemblyName System.Windows.Forms | Out-Null
    $dialog = New-Object System.Windows.Forms.OpenFileDialog
    $dialog.InitialDirectory = Split-Path $PSScriptRoot
    $dialog.Filter = "ELF Files (*.elf)|*.elf|All Files (*.*)|*.*"
    $dialog.Title = "Select firmware file to burn and verify"

    if ($dialog.ShowDialog() -ne [System.Windows.Forms.DialogResult]::OK) {
        Write-Host "No file selected. Aborting."
        exit 1
    }

    $FilePath = $dialog.FileName
}

if (-not (Test-Path $FilePath)) {
    Write-Error "Firmware file not found: $FilePath"
    exit 1
}

Write-Host "Burning and verifying firmware file: $FilePath"

$arguments = @(
    '-c', 'port=SWD',
    '-d', $FilePath,
    '-v',
    '-rst'
)

$process = Start-Process -FilePath $cli -ArgumentList $arguments -NoNewWindow -Wait -PassThru
if ($process.ExitCode -ne 0) {
    Write-Error "Programming/verification failed with exit code $($process.ExitCode)."
    exit $process.ExitCode
}

Write-Host "Programming and verification completed successfully."

