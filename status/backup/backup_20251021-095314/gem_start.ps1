# Startar Gem och AnythingLLM + loggar till log.txt
$logPath = "D:\Gem-Local\logs"
if (!(Test-Path $logPath)) { New-Item -ItemType Directory -Path $logPath | Out-Null }
$logFile = "$logPath\gem_log.txt"

function Log($text) {
    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    "$timestamp  $text" | Tee-Object -FilePath $logFile -Append
}

Log "=== Startsekvens initierad ==="

# Starta Ollama
if (-not (Get-Process -Name "ollama" -ErrorAction SilentlyContinue)) {
    try {
        Start-Process "C:\Program Files\Ollama\ollama.exe"
        Start-Sleep -Seconds 3
        Log "Ollama startad."
    } catch {
        Log "Fel: Kunde inte starta Ollama."
    }
} else {
    Log "Ollama körs redan."
}

# Starta AnythingLLM
$anythingPath = "C:\Users\$env:USERNAME\AppData\Local\Programs\AnythingLLM\AnythingLLM.exe"
if (Test-Path $anythingPath) {
    Start-Process $anythingPath
    Log "AnythingLLM startad."
} else {
    Log "Fel: Hittade inte AnythingLLM på standardplats."
}

# Öppna config-mappen
Start-Process "explorer.exe" "D:\Gem-Local\config"
Log "Gem-mapp öppnad. Start klar."

