# ═══════════════════════════════════════════════════════════
# 梦帮小助 v3.0 · 服务状态检查脚本 (PowerShell)
# ═══════════════════════════════════════════════════════════

Write-Host ""
Write-Host "  DREAMVFIA Dev Server Status" -ForegroundColor Red
Write-Host "  ===========================" -ForegroundColor Red
Write-Host ""

# Docker containers
Write-Host "  [Docker Containers]" -ForegroundColor Cyan
$dockerOut = docker ps --filter "name=dreamhelp" --format "table {{.Names}}\t{{.Status}}" 2>&1
if ($LASTEXITCODE -eq 0) {
    $dockerOut | ForEach-Object { Write-Host "    $_" }
}
else {
    Write-Host "    Docker not running" -ForegroundColor Yellow
}
Write-Host ""

# Port check
Write-Host "  [Service Ports]" -ForegroundColor Cyan
$ports = @(
    @{Name="PostgreSQL"; Port=5432},
    @{Name="Redis";      Port=6379},
    @{Name="Web Portal"; Port=3000},
    @{Name="Brain Core"; Port=8000},
    @{Name="Gateway";    Port=3100},
    @{Name="Milvus";     Port=19530},
    @{Name="ES";         Port=9200},
    @{Name="MinIO";      Port=9000}
)

foreach ($svc in $ports) {
    $tcp = New-Object System.Net.Sockets.TcpClient
    try {
        $tcp.Connect("localhost", $svc.Port)
        Write-Host ("    [OK] {0} :{1}" -f $svc.Name, $svc.Port) -ForegroundColor Green
        $tcp.Close()
    }
    catch {
        Write-Host ("    [--] {0} :{1}" -f $svc.Name, $svc.Port) -ForegroundColor DarkGray
    }
}
Write-Host ""

# WSL2 status
Write-Host "  [WSL2 Distros]" -ForegroundColor Cyan
wsl --list --verbose 2>&1 | ForEach-Object { Write-Host ("    " + $_) }
Write-Host ""
