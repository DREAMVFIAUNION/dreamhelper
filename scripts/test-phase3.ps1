# Phase 3 Integration Tests (Day 11-17)
# Tests: Session CRUD + Message Persistence + Completions Proxy + Skills API

$base = "http://localhost:3000"
$pass = 0
$fail = 0
$total = 0

function Test($name, $scriptBlock) {
    $script:total++
    try {
        $result = & $scriptBlock
        if ($result) {
            Write-Host "  [PASS] $name" -ForegroundColor Green
            $script:pass++
        } else {
            Write-Host "  [FAIL] $name" -ForegroundColor Red
            $script:fail++
        }
    } catch {
        Write-Host "  [FAIL] $name -- $($_.Exception.Message)" -ForegroundColor Red
        $script:fail++
    }
}

Write-Host "`n=== Phase 3 Integration Tests ===`n" -ForegroundColor Cyan

# -- 1. Register + Login --
Write-Host "[ Auth Setup ]" -ForegroundColor Yellow

$captchaRes = Invoke-RestMethod -Uri "$base/api/auth/captcha" -Method GET
$captchaId = $captchaRes.captchaId
$answer = $captchaRes.__test_answer

$ts = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$testEmail = "phase3test_${ts}@test.com"
$testUser = "p3user_${ts}"
$testPassword = "TestPass123!"

$verifyBody = @{ captchaId=$captchaId; answer=$answer } | ConvertTo-Json
$verifyRes = Invoke-RestMethod -Uri "$base/api/auth/captcha" -Method POST -ContentType "application/json" -Body $verifyBody
$verifyToken = $verifyRes.verifyToken

# Register - use Invoke-WebRequest to capture Set-Cookie
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$regBody = @{ email=$testEmail; username=$testUser; password=$testPassword; captchaVerifyToken=$verifyToken } | ConvertTo-Json

$regResponse = Invoke-WebRequest -Uri "$base/api/auth/register" -Method POST -ContentType "application/json" -Body $regBody -UseBasicParsing
# Extract token cookie from response
$setCookie = $regResponse.Headers["Set-Cookie"]
if ($setCookie) {
    foreach ($c in $setCookie) {
        if ($c -match "token=([^;]+)") {
            $tokenValue = $matches[1]
            $cookie = New-Object System.Net.Cookie("token", $tokenValue, "/", "localhost")
            $session.Cookies.Add($cookie)
        }
    }
}
Write-Host "  Auth: $testEmail registered" -ForegroundColor Gray

# -- 2. Session CRUD --
Write-Host "`n[ Session CRUD ]" -ForegroundColor Yellow

$sessionId = ""

Test "POST /api/chat/sessions -- create" {
    $res = Invoke-RestMethod -Uri "$base/api/chat/sessions" -Method POST -ContentType "application/json" -Body '{}' -WebSession $session
    $script:sessionId = $res.session.id
    $res.success -eq $true -and $res.session.id
}

Test "GET /api/chat/sessions -- list" {
    $res = Invoke-RestMethod -Uri "$base/api/chat/sessions" -Method GET -WebSession $session
    $res.success -eq $true -and $res.sessions.Count -ge 1
}

Test "GET /api/chat/sessions/[id] -- detail" {
    $res = Invoke-RestMethod -Uri "$base/api/chat/sessions/$sessionId" -Method GET -WebSession $session
    $res.success -eq $true -and $res.session.id -eq $sessionId
}

Test "PATCH /api/chat/sessions/[id] -- rename" {
    $body = @{ title="Test Session Renamed" } | ConvertTo-Json
    $res = Invoke-RestMethod -Uri "$base/api/chat/sessions/$sessionId" -Method PATCH -ContentType "application/json" -Body $body -WebSession $session
    $res.success -eq $true
}

# -- 3. Messages Persistence --
Write-Host "`n[ Messages Persistence ]" -ForegroundColor Yellow

Test "POST /api/chat/messages -- save 2 msgs" {
    $msgBody = '{"sessionId":"' + $sessionId + '","messages":[{"role":"user","content":"hello test"},{"role":"assistant","content":"hi reply"}]}'
    $res = Invoke-RestMethod -Uri "$base/api/chat/messages" -Method POST -ContentType "application/json" -Body $msgBody -WebSession $session
    $res.success -eq $true -and $res.count -eq 2
}

Test "GET /api/chat/sessions/[id] -- msgs persisted" {
    $res = Invoke-RestMethod -Uri "$base/api/chat/sessions/$sessionId" -Method GET -WebSession $session
    $res.session.messages.Count -eq 2
}

Test "Session auto-title generated" {
    $res = Invoke-RestMethod -Uri "$base/api/chat/sessions" -Method GET -WebSession $session
    $found = $res.sessions | Where-Object { $_.id -eq $sessionId }
    $found.title -and $found.title.Length -gt 0
}

# -- 4. Session Delete --
Write-Host "`n[ Session Delete ]" -ForegroundColor Yellow

$tmpId = ""
Test "DELETE /api/chat/sessions/[id] -- soft delete" {
    $tmpRes = Invoke-RestMethod -Uri "$base/api/chat/sessions" -Method POST -ContentType "application/json" -Body '{}' -WebSession $session
    $script:tmpId = $tmpRes.session.id
    $delRes = Invoke-RestMethod -Uri "$base/api/chat/sessions/$($script:tmpId)" -Method DELETE -WebSession $session
    $delRes.success -eq $true
}

Test "GET deleted session -- 404" {
    $got404 = $false
    try {
        $null = Invoke-WebRequest -Uri "$base/api/chat/sessions/$tmpId" -Method GET -WebSession $session -ErrorAction Stop
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 404) { $got404 = $true }
    }
    $got404
}

# -- 5. Skills API Proxy --
Write-Host "`n[ Skills API Proxy ]" -ForegroundColor Yellow

Test "GET /api/skills -- list or 502" {
    $ok = $false
    try {
        $null = Invoke-RestMethod -Uri "$base/api/skills" -Method GET -WebSession $session
        $ok = $true
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 502) { $ok = $true }
    }
    $ok
}

Test "POST /api/skills -- execute or 502" {
    $ok = $false
    try {
        $body = '{"name":"calculator","params":{"expression":"2+3*4"}}'
        $null = Invoke-RestMethod -Uri "$base/api/skills" -Method POST -ContentType "application/json" -Body $body -WebSession $session
        $ok = $true
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 502) { $ok = $true }
    }
    $ok
}

# -- 6. Auth Regression --
Write-Host "`n[ Auth Regression ]" -ForegroundColor Yellow

Test "GET /api/auth/me -- current user" {
    $res = Invoke-RestMethod -Uri "$base/api/auth/me" -Method GET -WebSession $session
    $res.success -eq $true -and $res.user.email -eq $testEmail
}

Test "PUT /api/auth/password -- wrong old password rejected" {
    $ok = $false
    try {
        $body = @{ currentPassword="WrongPass"; newPassword="NewPass123!" } | ConvertTo-Json
        $null = Invoke-WebRequest -Uri "$base/api/auth/password" -Method PUT -ContentType "application/json" -Body $body -WebSession $session -ErrorAction Stop
    } catch {
        $ok = $true
    }
    $ok
}

# -- 7. Completions Proxy --
Write-Host "`n[ Chat Completions Proxy ]" -ForegroundColor Yellow

Test "POST /api/chat/completions -- route exists" {
    $ok = $false
    try {
        $body = '{"session_id":"' + $sessionId + '","content":"hello","stream":false}'
        $null = Invoke-RestMethod -Uri "$base/api/chat/completions" -Method POST -ContentType "application/json" -Body $body -WebSession $session
        $ok = $true
    } catch {
        if ($_.Exception.Response.StatusCode.value__ -eq 502) { $ok = $true }
    }
    $ok
}

# -- 8. Admin Regression --
Write-Host "`n[ Admin Regression ]" -ForegroundColor Yellow

Test "POST /api/admin/auth/login -- non-admin rejected" {
    $ok = $false
    try {
        $body = @{ email=$testEmail; password=$testPassword } | ConvertTo-Json
        $null = Invoke-WebRequest -Uri "$base/api/admin/auth/login" -Method POST -ContentType "application/json" -Body $body -ErrorAction Stop
    } catch {
        $ok = $true
    }
    $ok
}

# -- Results --
Write-Host "`n===================================" -ForegroundColor Cyan
Write-Host "  Total: $total | Pass: $pass | Fail: $fail" -ForegroundColor $(if($fail -eq 0){"Green"}else{"Red"})
Write-Host "===================================`n" -ForegroundColor Cyan

exit $fail
