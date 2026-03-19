$base = 'http://localhost:3000'
$results = @()
function Test($cat, $name, $ok, $detail) {
  $script:results += [pscustomobject]@{Cat=$cat; Test=$name; Pass=[bool]$ok; Detail=$detail}
}

# ═══════════════════════════════════════════════════════════
# 5.1: FULL REGISTRATION FLOW
# ═══════════════════════════════════════════════════════════
Write-Host "`n===== 5.1: REGISTRATION FLOW =====" -ForegroundColor Cyan

$cap = Invoke-RestMethod "$base/api/auth/captcha"
Test 'E2E' '1. GET captcha => id+answer' ([bool]$cap.captchaId -and [bool]$cap.__test_answer) "id=$($cap.captchaId.Substring(0,8))..."

$vBody = @{captchaId=$cap.captchaId; answer=$cap.__test_answer} | ConvertTo-Json
$vr = Invoke-RestMethod "$base/api/auth/captcha" -Method POST -ContentType 'application/json' -Body $vBody
Test 'E2E' '2. POST captcha verify => token' ($vr.valid -and [bool]$vr.verifyToken) "valid=$($vr.valid)"
$verifyToken = $vr.verifyToken

$rnd = Get-Random -Maximum 999999
$testEmail = "e2e$rnd@test.com"
$testUser = "e2euser$rnd"
$testPass = "TestPass1A"
$regBody = @{email=$testEmail; username=$testUser; password=$testPass; captchaVerifyToken=$verifyToken} | ConvertTo-Json
$session = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$rr = Invoke-WebRequest "$base/api/auth/register" -Method POST -ContentType 'application/json' -Body $regBody -WebSession $session -SkipHttpErrorCheck
$rrJ = $rr.Content | ConvertFrom-Json
Test 'E2E' '3. Register new user => 201' ($rr.StatusCode -eq 201 -and $rrJ.success -eq $true) "status=$($rr.StatusCode) email=$($rrJ.user.email)"

$me = Invoke-WebRequest "$base/api/auth/me" -WebSession $session -SkipHttpErrorCheck
$meJ = $me.Content | ConvertFrom-Json
Test 'E2E' '4. GET /me after register => user' ($me.StatusCode -eq 200 -and $meJ.success) "email=$($meJ.user.email)"

$lo = Invoke-WebRequest "$base/api/auth/logout" -Method POST -WebSession $session -SkipHttpErrorCheck
Test 'E2E' '5. Logout => 200' ($lo.StatusCode -eq 200) "status=$($lo.StatusCode)"

$me2 = Invoke-WebRequest "$base/api/auth/me" -WebSession $session -SkipHttpErrorCheck
Test 'E2E' '6. /me after logout => 401' ($me2.StatusCode -eq 401) "status=$($me2.StatusCode)"

$s2 = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$lr = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body (@{email=$testEmail; password=$testPass} | ConvertTo-Json) -WebSession $s2 -SkipHttpErrorCheck
$lrJ = $lr.Content | ConvertFrom-Json
Test 'E2E' '7. Login registered user => 200' ($lr.StatusCode -eq 200 -and $lrJ.success) "email=$($lrJ.user.email)"

$me3 = Invoke-WebRequest "$base/api/auth/me" -WebSession $s2 -SkipHttpErrorCheck
$me3J = $me3.Content | ConvertFrom-Json
Test 'E2E' '8. /me after login => correct user' ($me3.StatusCode -eq 200 -and $me3J.user.email -eq $testEmail) "email=$($me3J.user.email)"

# ═══════════════════════════════════════════════════════════
# 5.2: ROUTE GUARD TESTS
# ═══════════════════════════════════════════════════════════
Write-Host "`n===== 5.2: ROUTE GUARD =====" -ForegroundColor Cyan

$pages = @('/', '/features', '/pricing', '/about')
foreach ($p in $pages) {
  try {
    $r = Invoke-WebRequest "$base$p" -SkipHttpErrorCheck
    Test 'ROUTE' "Public $p => 200" ($r.StatusCode -eq 200) "status=$($r.StatusCode)"
  } catch { Test 'ROUTE' "Public $p => 200" $false $_.Exception.Message }
}

$protected = @('/overview', '/chat', '/agents', '/knowledge', '/analytics', '/settings')
$unauthSess = New-Object Microsoft.PowerShell.Commands.WebRequestSession
foreach ($p in $protected) {
  try {
    $r = Invoke-WebRequest "$base$p" -WebSession $unauthSess -SkipHttpErrorCheck -MaximumRedirection 0
    Test 'ROUTE' "Protected $p unauth => 307" ($r.StatusCode -eq 307) "status=$($r.StatusCode)"
  } catch {
    $sc = $_.Exception.Response.StatusCode.value__
    Test 'ROUTE' "Protected $p unauth => 307" ($sc -eq 307) "status=$sc"
  }
}

# Logged-in user accessing /login => redirect to /overview
try {
  $r = Invoke-WebRequest "$base/login" -WebSession $s2 -SkipHttpErrorCheck -MaximumRedirection 0
  Test 'ROUTE' 'Auth /login with token => 307' ($r.StatusCode -eq 307) "status=$($r.StatusCode)"
} catch {
  $sc = $_.Exception.Response.StatusCode.value__
  Test 'ROUTE' 'Auth /login with token => 307' ($sc -eq 307) "status=$sc"
}

# ═══════════════════════════════════════════════════════════
# 5.3: SECURITY TESTS
# ═══════════════════════════════════════════════════════════
Write-Host "`n===== 5.3: SECURITY =====" -ForegroundColor Cyan

# Invalid JWT token
$fakeSess = New-Object Microsoft.PowerShell.Commands.WebRequestSession
$fakeCookie = New-Object System.Net.Cookie('token', 'fake.jwt.token', '/', 'localhost')
$fakeSess.Cookies.Add($fakeCookie)
$fakeMe = Invoke-WebRequest "$base/api/auth/me" -WebSession $fakeSess -SkipHttpErrorCheck
Test 'SEC' '1. Fake JWT => 401' ($fakeMe.StatusCode -eq 401) "status=$($fakeMe.StatusCode)"

# XSS in email
$xssBody = @{email='<script>alert(1)</script>@test.com'; password='Test1234'} | ConvertTo-Json
$xr = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body $xssBody -SkipHttpErrorCheck
$xrJ = $xr.Content | ConvertFrom-Json
$hasScript = $xr.Content -match '<script>'
Test 'SEC' '2. XSS in email => no script in response' (-not $hasScript) "hasScript=$hasScript status=$($xr.StatusCode)"

# XSS in username (register)
$cap2 = Invoke-RestMethod "$base/api/auth/captcha"
$vr2 = Invoke-RestMethod "$base/api/auth/captcha" -Method POST -ContentType 'application/json' -Body (@{captchaId=$cap2.captchaId; answer=$cap2.__test_answer} | ConvertTo-Json)
$xssReg = @{email="xss$rnd@test.com"; username='<img onerror=alert(1)>'; password='TestPass1A'; captchaVerifyToken=$vr2.verifyToken} | ConvertTo-Json
$xrr = Invoke-WebRequest "$base/api/auth/register" -Method POST -ContentType 'application/json' -Body $xssReg -SkipHttpErrorCheck
Test 'SEC' '3. XSS username => rejected (400)' ($xrr.StatusCode -eq 400) "status=$($xrr.StatusCode)"

# Replay captcha token (already consumed)
$replayReg = @{email="replay$rnd@test.com"; username="replay$rnd"; password='TestPass1A'; captchaVerifyToken=$verifyToken} | ConvertTo-Json
$replay = Invoke-WebRequest "$base/api/auth/register" -Method POST -ContentType 'application/json' -Body $replayReg -SkipHttpErrorCheck
Test 'SEC' '4. Replay captcha token => 400' ($replay.StatusCode -eq 400) "status=$($replay.StatusCode)"

# Wrong password multiple times (account not locked after <5)
for ($i = 0; $i -lt 3; $i++) {
  Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body (@{email=$testEmail; password='WrongPass1'} | ConvertTo-Json) -SkipHttpErrorCheck | Out-Null
}
$stillLogin = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body (@{email=$testEmail; password=$testPass} | ConvertTo-Json) -SkipHttpErrorCheck
$slJ = $stillLogin.Content | ConvertFrom-Json
Test 'SEC' '5. Correct password after 3 fails => 200' ($stillLogin.StatusCode -eq 200 -and $slJ.success) "status=$($stillLogin.StatusCode)"

# ═══════════════════════════════════════════════════════════
# 5.4: BOUNDARY TESTS
# ═══════════════════════════════════════════════════════════
Write-Host "`n===== 5.4: BOUNDARY =====" -ForegroundColor Cyan

# Empty fields
$empty = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body '{}' -SkipHttpErrorCheck
Test 'BOUND' '1. Login empty body => 400' ($empty.StatusCode -eq 400) "status=$($empty.StatusCode)"

$empty2 = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body '{"email":"","password":""}' -SkipHttpErrorCheck
Test 'BOUND' '2. Login empty strings => 400' ($empty2.StatusCode -eq 400) "status=$($empty2.StatusCode)"

# Super long email
$longEmail = ('a' * 300) + '@test.com'
$longR = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body (@{email=$longEmail; password='Test1234'} | ConvertTo-Json) -SkipHttpErrorCheck
Test 'BOUND' '3. Long email => 401 (not 500)' ($longR.StatusCode -ne 500) "status=$($longR.StatusCode)"

# Password too short (register)
$cap3 = Invoke-RestMethod "$base/api/auth/captcha"
$vr3 = Invoke-RestMethod "$base/api/auth/captcha" -Method POST -ContentType 'application/json' -Body (@{captchaId=$cap3.captchaId; answer=$cap3.__test_answer} | ConvertTo-Json)
$shortPw = @{email="short$rnd@test.com"; username="shortpw$rnd"; password='Ab1'; captchaVerifyToken=$vr3.verifyToken} | ConvertTo-Json
$spr = Invoke-WebRequest "$base/api/auth/register" -Method POST -ContentType 'application/json' -Body $shortPw -SkipHttpErrorCheck
Test 'BOUND' '4. Short password => 400' ($spr.StatusCode -eq 400) "status=$($spr.StatusCode)"

# Duplicate email
$cap4 = Invoke-RestMethod "$base/api/auth/captcha"
$vr4 = Invoke-RestMethod "$base/api/auth/captcha" -Method POST -ContentType 'application/json' -Body (@{captchaId=$cap4.captchaId; answer=$cap4.__test_answer} | ConvertTo-Json)
$dupReg = @{email=$testEmail; username="dup$rnd"; password='TestPass1A'; captchaVerifyToken=$vr4.verifyToken} | ConvertTo-Json
$dup = Invoke-WebRequest "$base/api/auth/register" -Method POST -ContentType 'application/json' -Body $dupReg -SkipHttpErrorCheck
Test 'BOUND' '5. Duplicate email => 409' ($dup.StatusCode -eq 409) "status=$($dup.StatusCode)"

# Duplicate username
$cap5 = Invoke-RestMethod "$base/api/auth/captcha"
$vr5Body = @{captchaId=$cap5.captchaId; answer=$cap5.__test_answer} | ConvertTo-Json
$vr5 = Invoke-RestMethod "$base/api/auth/captcha" -Method POST -ContentType 'application/json' -Body $vr5Body
if (-not $vr5.verifyToken) {
  Test 'BOUND' '6. Duplicate username => 409' $false "captcha verify failed: $($vr5 | ConvertTo-Json -Compress)"
} else {
  $dupU = @{email="dupuser$rnd@test.com"; username=$testUser; password='TestPass1A'; captchaVerifyToken=$vr5.verifyToken} | ConvertTo-Json
  $dupUr = Invoke-WebRequest "$base/api/auth/register" -Method POST -ContentType 'application/json' -Body $dupU -SkipHttpErrorCheck
  Test 'BOUND' '6. Duplicate username => 409' ($dupUr.StatusCode -eq 409) "status=$($dupUr.StatusCode) body=$($dupUr.Content)"
}

# Invalid JSON body
$badJ = Invoke-WebRequest "$base/api/auth/login" -Method POST -ContentType 'application/json' -Body 'not-json' -SkipHttpErrorCheck
Test 'BOUND' '7. Invalid JSON => not 500' ($badJ.StatusCode -ne 500) "status=$($badJ.StatusCode)"

# ═══════════════════════════════════════════════════════════
# SUMMARY
# ═══════════════════════════════════════════════════════════
Write-Host "`n===== RESULTS =====" -ForegroundColor Yellow
$results | Format-Table Cat, Test, Pass, Detail -AutoSize

$passed = ($results | Where-Object { $_.Pass }).Count
$total = $results.Count
$failed = $results | Where-Object { -not $_.Pass }

Write-Host "`n================================" -ForegroundColor $(if($passed -eq $total){'Green'}else{'Red'})
Write-Host "  TOTAL: $passed / $total PASSED" -ForegroundColor $(if($passed -eq $total){'Green'}else{'Red'})
Write-Host "================================" -ForegroundColor $(if($passed -eq $total){'Green'}else{'Red'})

if ($failed.Count -gt 0) {
  Write-Host "`nFAILED TESTS:" -ForegroundColor Red
  $failed | ForEach-Object { Write-Host "  X [$($_.Cat)] $($_.Test) - $($_.Detail)" -ForegroundColor Red }
}
