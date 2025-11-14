# PowerShell script to find Raspberry Pi on network
# Run this from PowerShell: .\find_pi.ps1

param(
    [string]$Network = "172.20.10",
    [int]$StartIP = 2,
    [int]$EndIP = 14
)

Write-Host "🔍 Scanning for Raspberry Pi on network $Network.0/28..." -ForegroundColor Cyan
Write-Host "Testing IPs from $Network.$StartIP to $Network.$EndIP" -ForegroundColor Yellow
Write-Host ""

$found = $false

for ($i = $StartIP; $i -le $EndIP; $i++) {
    $ip = "$Network.$i"
    Write-Host "Testing $ip..." -NoNewline

    try {
        $ping = Test-Connection -ComputerName $ip -Count 1 -Quiet -TimeoutSeconds 1
        if ($ping) {
            Write-Host " ✓ ALIVE" -ForegroundColor Green

            # Try to get hostname
            try {
                $hostname = [System.Net.Dns]::GetHostEntry($ip).HostName
                Write-Host "  Hostname: $hostname" -ForegroundColor Green

                # Check if it looks like a Raspberry Pi
                if ($hostname -like "*raspberry*" -or $hostname -eq "pi") {
                    Write-Host "  🎉 Found Raspberry Pi at $ip ($hostname)" -ForegroundColor Green -BackgroundColor Black
                    $found = $true
                }
            } catch {
                Write-Host "  Could not resolve hostname" -ForegroundColor Yellow
            }

            # Try SSH connection test
            try {
                $sshTest = Test-NetConnection -ComputerName $ip -Port 22 -WarningAction SilentlyContinue
                if ($sshTest.TcpTestSucceeded) {
                    Write-Host "  🔐 SSH port open" -ForegroundColor Green
                } else {
                    Write-Host "  ❌ SSH port closed" -ForegroundColor Red
                }
            } catch {
                Write-Host "  Could not test SSH" -ForegroundColor Yellow
            }

        } else {
            Write-Host " ❌ No response" -ForegroundColor Red
        }
    } catch {
        Write-Host " ❌ Error testing $ip" -ForegroundColor Red
    }
}

Write-Host ""
if (-not $found) {
    Write-Host "❌ No Raspberry Pi found in the scanned range." -ForegroundColor Red
    Write-Host ""
    Write-Host "Troubleshooting steps:" -ForegroundColor Yellow
    Write-Host "1. Make sure Raspberry Pi is powered on" -ForegroundColor White
    Write-Host "2. Check Ethernet cable is connected" -ForegroundColor White
    Write-Host "3. Try different IP ranges if your network is different" -ForegroundColor White
    Write-Host "4. Check router admin panel for connected devices" -ForegroundColor White
    Write-Host "5. Try connecting Pi directly to computer via Ethernet" -ForegroundColor White
} else {
    Write-Host "✅ Raspberry Pi found! Use the IP address above for SSH/scp commands." -ForegroundColor Green
}