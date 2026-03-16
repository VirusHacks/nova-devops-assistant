# InfraGuard ngrok Tunnel Startup Script
# This script starts an ngrok tunnel on port 8000.
# If NGROK_DOMAIN is set in .env, it uses that for a permanent URL.

Write-Host "--- Starting Nova-Devops-Automate ngrok Tunnel ---" -ForegroundColor Cyan

# 1. Kill any existing ngrok processes to avoid "session limit" errors
Write-Host "Cleaning up existing ngrok sessions..." -ForegroundColor Gray
taskkill /f /im ngrok.exe 2>$null | Out-Null

# 2. Load .env variables correctly into the process atmosphere
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        # Match lines like KEY=VALUE, ignoring comments and spaces
        if ($_ -match "^\s*([^#\s=]+)\s*=\s*([^#]*)\s*$") {
            $key = $Matches[1].Trim()
            $value = $Matches[2].Trim()
            # Remove quotes if present
            $value = $value -replace "^['""]|['""]$", ""
            # Set environment variable for the current process
            Set-Item -Path "env:$key" -Value $value
            # Also set it for any child processes (like ngrok)
            [System.Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

# 3. Apply Auth Token if present
if ($env:NGROK_AUTHTOKEN) {
    ngrok config add-authtoken $env:NGROK_AUTHTOKEN | Out-Null
    Write-Host "Applied ngrok authtoken." -ForegroundColor Gray
}

# 4. Determine arguments
$ngrokArgs = "http 8000"
if ($env:NGROK_DOMAIN) {
    $domain = $env:NGROK_DOMAIN.Trim()
    # Ensure no http:// prefix or /webhook path in the domain variable
    $domain = $domain -replace "^https?://", ""
    $domain = $domain -replace "/.*$", ""
    
    $ngrokArgs += " --url=$domain"
    Write-Host "Using static domain: $domain" -ForegroundColor Yellow
}

# 5. Start ngrok in the background
$proc = Start-Process ngrok -ArgumentList $ngrokArgs -PassThru -WindowStyle Hidden

Write-Host "Waiting for ngrok to initialize..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# 6. Fetch the public URL from ngrok's local API
try {
    $response = Invoke-RestMethod -Uri "http://localhost:4040/api/tunnels"
    if ($response.tunnels.Count -eq 0) {
        Write-Host "Error: No tunnels found. Check if your ngrok token/domain is valid." -ForegroundColor Red
    } else {
        $publicUrl = $response.tunnels[0].public_url
        Write-Host "`n================================================" -ForegroundColor Green
        Write-Host " PUBLIC WEBHOOK URL: " -NoNewline
        Write-Host "$($publicUrl.TrimEnd('/'))/webhook/github" -ForegroundColor Yellow -BackgroundColor Black
        Write-Host "================================================`n" -ForegroundColor Green
        
        Write-Host "1. Go to your GitHub App settings (Nova-Devops-Automate)."
        Write-Host "2. Ensure 'Webhook URL' is set to the yellow URL above."
        Write-Host "3. Ensure your local server is running on port 8000."
        Write-Host "`nKEEP THIS WINDOW OPEN to keep the tunnel alive." -ForegroundColor Gray
        Write-Host "Press any key to stop the tunnel..." -ForegroundColor Gray
        $null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
    }
} catch {
    Write-Host "Error: Failed to connect to ngrok local API. Is ngrok running?" -ForegroundColor Red
} finally {
    if ($proc) {
        Stop-Process -Id $proc.Id -ErrorAction SilentlyContinue
        Write-Host "Tunnel stopped." -ForegroundColor Cyan
    }
}
