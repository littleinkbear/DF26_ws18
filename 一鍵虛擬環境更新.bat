@echo off
REM ===== ASCII batch bootstrap (cmd never parses the Chinese below) =====
set "PROJROOT=%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -Command "$t=[IO.File]::ReadAllText('%~f0',[Text.Encoding]::UTF8); $m='#PS'+'START'; Invoke-Expression ($t.Substring($t.IndexOf($m)+$m.Length))"
exit /b
#PSSTART
# ============================================================
#  一键更新虚拟环境检查（单文件 · 双击即可运行）
#   1. 检测全局是否有 Python 3.14，无则用 winget 自动安装
#   2. 检查项目 .venv 是否为 3.14，不符则删除重建
#   3. 升级 pip 并安装 / 更新 requirements.txt
#   4. 某个包固定版本失败 -> 自动改用不固定版本重试；仍失败 -> 红字警告
#  可重复运行；requirements.txt 更新后再双击一次即可同步。
# ============================================================

try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
$ErrorActionPreference = 'Continue'

$PYVER  = '3.14'
$PYFULL = '3.14.6'
$ROOT  = $env:PROJROOT
if (-not $ROOT) { $ROOT = (Get-Location).Path }
$ROOT  = $ROOT.TrimEnd('\')
$VENV  = Join-Path $ROOT '.venv'
$VPY   = Join-Path $VENV 'Scripts\python.exe'
$REQ   = Join-Path $ROOT 'requirements.txt'

function Info($m){ Write-Host $m -ForegroundColor Cyan }
function Ok($m)  { Write-Host $m -ForegroundColor Green }
function Warn($m){ Write-Host $m -ForegroundColor Yellow }
function Err($m) { Write-Host $m -ForegroundColor Red }
function Finish($code){
    Write-Host ""
    try { Read-Host "按 Enter 键关闭窗口" | Out-Null } catch {}
    exit $code
}

# ---- 进度条工具 ----
$BARW = 30
function Draw-Bar([int]$pct,[string]$label){
    if ($pct -lt 0) { $pct = 0 }; if ($pct -gt 100) { $pct = 100 }
    $f = [int]($BARW * $pct / 100)
    $bar = ('#' * $f) + ('-' * ($BARW - $f))
    Write-Host -NoNewline ("`r    {0} [{1}] {2,3}%" -f $label, $bar, $pct) -ForegroundColor Cyan
}

# 真实百分比下载（已知文件总大小）
function Download-WithBar($url, $out, $label){
    try {
        $req  = [System.Net.HttpWebRequest]::Create($url)
        $req.UserAgent = 'venv-bootstrap'
        $resp = $req.GetResponse()
        $total = $resp.ContentLength
        $in  = $resp.GetResponseStream()
        $fs  = [IO.File]::Create($out)
        $buf = New-Object byte[] 1048576
        $sum = 0; $read = 0
        while (($read = $in.Read($buf, 0, $buf.Length)) -gt 0) {
            $fs.Write($buf, 0, $read); $sum += $read
            if ($total -gt 0) { Draw-Bar ([int]($sum * 100 / $total)) $label }
        }
        $fs.Close(); $in.Close(); $resp.Close()
        Draw-Bar 100 $label; Write-Host ""
        return $true
    } catch {
        Write-Host ""
        Err "[错误] 下载安装包失败：$($_.Exception.Message)"
        return $false
    }
}

# 不确定耗时的等待（来回跑马灯），$cond 为 $true 时持续动画
function Wait-WithMarquee([scriptblock]$cond, [string]$label){
    $pos = 0; $dir = 1
    while (& $cond) {
        $cells = ,'-' * $BARW
        $cells[$pos] = '#'
        Write-Host -NoNewline ("`r    {0} [{1}]" -f $label, (-join $cells)) -ForegroundColor Cyan
        Start-Sleep -Milliseconds 120
        $pos += $dir
        if ($pos -ge $BARW - 1) { $dir = -1 } elseif ($pos -le 0) { $dir = 1 }
    }
    Write-Host ("`r    {0} [{1}] 完成" -f $label, ('#' * $BARW)) -ForegroundColor Green
}

Info "[项目根目录] $ROOT"
Write-Host ""

# ---- 安装官方安装包（winget 不可用时的回退方案） ----
function Install-PythonOfficial {
    $url = "https://www.python.org/ftp/python/$PYFULL/python-$PYFULL-amd64.exe"
    $exe = Join-Path $env:TEMP "python-$PYFULL-amd64.exe"
    Info "    从 python.org 下载安装包 $PYFULL ..."
    if (-not (Download-WithBar $url $exe "下载")) {
        Err "       请手动安装 https://www.python.org/downloads/"
        return $false
    }
    Info "    静默安装中（含 py 启动器，请稍候）..."
    $p = Start-Process -FilePath $exe -PassThru -ArgumentList `
        '/quiet','InstallAllUsers=0','PrependPath=1','Include_launcher=1','InstallLauncherAllUsers=1'
    Wait-WithMarquee { -not $p.HasExited } "安装"
    Remove-Item $exe -Force -ErrorAction SilentlyContinue
    if ($p.ExitCode -ne 0) {
        Err "[错误] 安装程序返回错误码 $($p.ExitCode)。"
        return $false
    }
    return $true
}

# ---- 1. 确认全局有 Python 3.14 ----
Info "[1/4] 检查全局 Python $PYVER ..."
& py "-$PYVER" --version *> $null
if ($LASTEXITCODE -ne 0) {
    Warn "    找不到 Python $PYVER，尝试自动安装..."
    $installed = $false
    if (Get-Command winget -ErrorAction SilentlyContinue) {
        Info "    使用 winget 安装..."
        winget install --id Python.Python.3.14 -e --source winget --accept-package-agreements --accept-source-agreements
        & py "-$PYVER" --version *> $null
        if ($LASTEXITCODE -eq 0) { $installed = $true }
        else { Warn "    winget 安装未生效，改用官方安装包回退方案..." }
    } else {
        Warn "    找不到 winget，改用官方安装包回退方案..."
    }
    if (-not $installed) {
        if (Install-PythonOfficial) {
            & py "-$PYVER" --version *> $null
            if ($LASTEXITCODE -eq 0) { $installed = $true }
        }
    }
    if (-not $installed) {
        Err "[错误] Python $PYVER 安装后仍无法调用。"
        Err "       请关闭并重开此窗口后再双击运行一次。"
        Finish 1
    }
}
$gv = (& py "-$PYVER" --version) 2>&1
Ok  "    全局 $gv"
Write-Host ""

# ---- 2. 检查现有 .venv 版本是否正确 ----
Info "[2/4] 检查 .venv ..."
$needCreate = $true
if (Test-Path $VPY) {
    $cur = (& $VPY --version) 2>&1
    Write-Host "    现有 .venv $cur"
    if ("$cur" -match [regex]::Escape("Python $PYVER.")) {
        $needCreate = $false
    } else {
        Warn "    版本不符 $PYVER，删除重建..."
        Remove-Item $VENV -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# ---- 3. 创建 .venv ----
if ($needCreate) {
    Info "[3/4] 用 Python $PYVER 创建 .venv ..."
    $vp = Start-Process -FilePath "py" -ArgumentList "-$PYVER","-m","venv","$VENV" -PassThru -NoNewWindow
    Wait-WithMarquee { -not $vp.HasExited } "创建虚拟环境"
    if ($vp.ExitCode -ne 0 -or -not (Test-Path $VPY)) {
        Err "[错误] 创建虚拟环境失败。"
        Finish 1
    }
} else {
    Info "[3/4] .venv 已是 $PYVER，跳过创建。"
}
Write-Host ""

# ---- 4. 安装 / 更新 requirements ----
Info "[4/4] 升级 pip 并安装 / 更新软件包 ..."
& $VPY -m pip install --upgrade pip
if (-not (Test-Path $REQ)) {
    Warn "[警告] 找不到 requirements.txt，跳过软件包安装。"
    Ok "完成。虚拟环境就绪 $VENV"
    Finish 0
}

Info "    先尝试按 requirements.txt 整体安装 ..."
& $VPY -m pip install -r $REQ
if ($LASTEXITCODE -eq 0) {
    Write-Host ""
    Ok "============================================================"
    Ok " 完成。虚拟环境就绪 $VENV"
    Ok " 启动命令 .venv\Scripts\activate"
    Ok "============================================================"
    Finish 0
}

Write-Host ""
Warn "    整体安装失败，改为逐行安装；某行失败时自动改用不固定版本重试 ..."
$failed = @()
foreach ($raw in Get-Content $REQ) {
    $line = $raw.Trim()
    if ($line -eq '' -or $line.StartsWith('#')) { continue }

    & $VPY -m pip install $line
    if ($LASTEXITCODE -ne 0) {
        $pkg = ($line -split '[<>=!~; \[]')[0]
        Warn "       固定版本失败，改用不固定版本重试 $pkg"
        & $VPY -m pip install $pkg
        if ($LASTEXITCODE -ne 0) {
            $failed += $pkg
        }
    }
}

if ($failed.Count -gt 0) {
    Write-Host ""
    Err "============================================================"
    Err "[错误] 以下软件包安装失败（固定与不固定版本均失败）:"
    Err ("   " + ($failed -join '  '))
    Err "请手动检查网络 / 包名 / requirements.txt 后重试。"
    Err "============================================================"
    Finish 1
}

Write-Host ""
Ok "============================================================"
Ok " 完成。虚拟环境就绪 $VENV"
Ok " 启动命令 .venv\Scripts\activate"
Ok "============================================================"
Finish 0
