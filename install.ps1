<#
  Installer for the ZZ_SWFOC engine patch (EAW Engine Ability Extension)
  Star Wars: Empire at War - Forces of Corruption, 64-bit Steam build. Windows PowerShell 5.1 or newer.

  Easiest: double-click Install.bat (or Uninstall.bat / Status.bat) in the same folder.

  powershell -ExecutionPolicy Bypass -File install.ps1 [-Uninstall] [-Status] [-GameDir <path>] [-Dll <file>] [-Force]

  install    copies ZZ_SWFOC.dll into the game's corruption\ folder and renames StarWarsG.exe's one import
             POWRPROF.dll -> ZZ_SWFOC.dll (same length; nothing else changes). The untouched exe is backed up
             first as StarWarsG.exe.zz_original.
  -Uninstall puts the POWRPROF.dll import back and removes ZZ_SWFOC.dll.
  -Status    shows what is installed.
  Steam's "Verify integrity of game files" and game updates restore the original exe: run Install again afterwards.
#>
param(
    [switch]$Uninstall,
    [switch]$Status,
    [string]$GameDir,
    [string]$SteamRoot,
    [string]$Dll,
    [switch]$Force
)
$ErrorActionPreference = 'Stop'

$DllName = 'ZZ_SWFOC.dll'
$ExeName = 'StarWarsG.exe'
$OldName = 'POWRPROF.dll'
$NewName = 'ZZ_SWFOC.dll'
$BackupSuffix = '.zz_original'
$GameFolder = 'Star Wars Empire at War'
$KnownExes = @{
    '07DAEEAEC9D1E751383B1DB3F5847B6C66F68785440A6C52C87B85F723D018A4' = 'stock'
    'F3C1FA3AF132AFC17E4E606BE2874BC3DE9D42B4BFF4FCCDF0E16DE2005FA917' = 'patched'
}
$Here = Split-Path -Parent $MyInvocation.MyCommand.Path

function Fail([string]$msg) { throw [System.Exception]::new($msg) }

function Get-Sha256Bytes([byte[]]$bytes) {
    $sha = [System.Security.Cryptography.SHA256]::Create()
    try { return (($sha.ComputeHash($bytes) | ForEach-Object { $_.ToString('X2') }) -join '') }
    finally { $sha.Dispose() }
}
function Get-Sha256File([string]$path) { return (Get-FileHash -Algorithm SHA256 -LiteralPath $path).Hash.ToUpper() }

# ------------------------------------------------------------------ PE import table
function Get-ImportName([byte[]]$b) {
    if ($b.Length -lt 0x40 -or $b[0] -ne 0x4D -or $b[1] -ne 0x5A) { Fail 'not an exe file' }
    $pe = [long][BitConverter]::ToUInt32($b, 0x3c)
    if ([BitConverter]::ToUInt32($b, [int]$pe) -ne 0x4550) { Fail 'not a PE file' }
    $opt = $pe + 24
    if ([BitConverter]::ToUInt16($b, [int]$opt) -ne 0x20b) { Fail 'not a 64-bit exe (this patch is for the 64-bit Steam build)' }
    $nsec = [long][BitConverter]::ToUInt16($b, [int]($pe + 6))
    $secTab = $opt + [long][BitConverter]::ToUInt16($b, [int]($pe + 20))
    $secs = @()
    for ($i = 0; $i -lt $nsec; $i++) {
        $s = $secTab + 40 * $i + 8
        $secs += ,@([long][BitConverter]::ToUInt32($b, [int]$s), [long][BitConverter]::ToUInt32($b, [int]($s + 4)),
                    [long][BitConverter]::ToUInt32($b, [int]($s + 8)), [long][BitConverter]::ToUInt32($b, [int]($s + 12)))
    }
    $toOff = {
        param([long]$rva)
        foreach ($s in $secs) {
            $size = [Math]::Max($s[0], $s[2])
            if ($rva -ge $s[1] -and $rva -lt ($s[1] + $size)) { return $s[3] + $rva - $s[1] }
        }
        Fail ('import table points outside the exe (rva 0x{0:x})' -f $rva)
    }
    $d = & $toOff ([long][BitConverter]::ToUInt32($b, [int]($opt + 120)))
    $hits = @(); $all = @()
    while ($true) {
        $nameRva = [long][BitConverter]::ToUInt32($b, [int]($d + 12))
        if ($nameRva -eq 0) { break }
        $n = & $toOff $nameRva
        $e = $n; while ($b[[int]$e] -ne 0) { $e++ }
        $name = [System.Text.Encoding]::ASCII.GetString($b, [int]$n, [int]($e - $n))
        $all += $name
        if ($name -ieq $OldName -or $name -ieq $NewName) { $hits += ,@($n, $name) }
        $d += 20
    }
    if ($hits.Count -ne 1) { Fail ('expected one POWRPROF.dll import, found: ' + ($all -join ', ')) }
    return $hits[0]
}

function Get-ExeState([string]$exe) {
    $b = [System.IO.File]::ReadAllBytes($exe)
    $h = Get-Sha256Bytes $b
    $imp = Get-ImportName $b
    return @{ Bytes = $b; Hash = $h; Offset = [int]$imp[0]; Name = $imp[1] }
}

function Describe($st) {
    $kind = $KnownExes[$st.Hash]
    if ($kind) { return "$kind 1.121.859328 (imports $($st.Name))" }
    return "unknown version (imports $($st.Name))"
}

function Set-ImportName([string]$exe, $st, [string]$name) {
    $b = $st.Bytes
    $nb = [System.Text.Encoding]::ASCII.GetBytes($name)
    [Array]::Copy($nb, 0, $b, $st.Offset, $nb.Length)
    $tmp = Join-Path (Split-Path -Parent $exe) ('.zz_tmp_' + [Guid]::NewGuid().ToString('N'))
    [System.IO.File]::WriteAllBytes($tmp, $b)
    Move-Item -LiteralPath $tmp -Destination $exe -Force
}

# ------------------------------------------------------------------ finding the game
function Get-SteamRoots {
    $roots = @()
    if ($SteamRoot) { $roots += $SteamRoot }
    foreach ($k in @(@('HKCU:\Software\Valve\Steam', 'SteamPath'),
                     @('HKLM:\SOFTWARE\WOW6432Node\Valve\Steam', 'InstallPath'),
                     @('HKLM:\SOFTWARE\Valve\Steam', 'InstallPath'))) {
        try { $v = (Get-ItemProperty -Path $k[0] -Name $k[1] -ErrorAction Stop).($k[1]); if ($v) { $roots += $v } } catch { }
    }
    foreach ($envName in @('ProgramFiles(x86)', 'ProgramFiles')) {
        $p = [Environment]::GetEnvironmentVariable($envName)
        if ($p) { $roots += (Join-Path $p 'Steam') }
    }
    return $roots
}

function Get-SteamLibraries {
    $libs = @()
    foreach ($r in Get-SteamRoots) {
        if (-not (Test-Path -LiteralPath $r -PathType Container)) { continue }
        $libs += $r
        $vdf = Join-Path $r 'steamapps\libraryfolders.vdf'
        if (Test-Path -LiteralPath $vdf) {
            $text = [System.IO.File]::ReadAllText($vdf)
            foreach ($m in [regex]::Matches($text, '"path"\s+"([^"]+)"')) { $libs += $m.Groups[1].Value.Replace('\\', '\') }
        }
    }
    $seen = @{}; $out = @()
    foreach ($l in $libs) {
        $key = $l.Replace('/', '\').TrimEnd('\').ToLower()
        if (-not $seen.ContainsKey($key)) { $seen[$key] = 1; $out += $l }
    }
    return $out
}

function Get-CorruptionDir([string]$path) {
    foreach ($d in @((Join-Path $path 'corruption'), $path)) {
        if (Test-Path -LiteralPath (Join-Path $d $ExeName) -PathType Leaf) { return (Resolve-Path -LiteralPath $d).Path }
    }
    return $null
}

function Find-Game {
    if ($GameDir) {
        $d = Get-CorruptionDir $GameDir
        if (-not $d) { Fail "no corruption\$ExeName under $GameDir" }
        return $d
    }
    $found = @()
    foreach ($lib in Get-SteamLibraries) {
        $d = Get-CorruptionDir (Join-Path $lib "steamapps\common\$GameFolder")
        if ($d -and ($found -notcontains $d)) { $found += $d }
    }
    if ($found.Count -eq 0) {
        Fail "could not find `"$GameFolder`" in any Steam library. Run again with -GameDir `"<path to the game folder>`""
    }
    if ($found.Count -gt 1) { Fail ("found more than one install, pick one with -GameDir:`n  " + ($found -join "`n  ")) }
    return $found[0]
}

function Find-Dll {
    $cands = @()
    if ($Dll) { $cands += $Dll } else { $cands += (Join-Path $Here $DllName); $cands += (Join-Path $Here "dll\$DllName") }
    foreach ($c in $cands) { if (Test-Path -LiteralPath $c -PathType Leaf) { return (Resolve-Path -LiteralPath $c).Path } }
    Fail ("$DllName not found next to the installer (looked for: " + ($cands -join ', ') + ')')
}

# ------------------------------------------------------------------ commands
function Do-Status {
    $game = Find-Game
    $exe = Join-Path $game $ExeName
    $st = Get-ExeState $exe
    $dst = Join-Path $game $DllName
    Write-Host "game folder: $game"
    Write-Host ("exe:         " + (Describe $st))
    if (Test-Path -LiteralPath $dst) {
        $state = 'present'
        try { if ((Get-Sha256File $dst) -eq (Get-Sha256File (Find-Dll))) { $state += ', same as the bundled one' } else { $state += ', differs from the bundled one' } } catch { }
        Write-Host "dll:         $state"
    } else { Write-Host 'dll:         not installed' }
    $bak = $exe + $BackupSuffix
    if (Test-Path -LiteralPath $bak) { Write-Host "exe backup:  $ExeName$BackupSuffix" } else { Write-Host 'exe backup:  none' }
    if (($st.Name -ieq $NewName) -and (Test-Path -LiteralPath $dst)) { Write-Host '=> engine patch is INSTALLED' -ForegroundColor Green }
    else { Write-Host '=> engine patch is NOT installed' -ForegroundColor Yellow }
}

function Do-Install {
    $game = Find-Game
    $src = Find-Dll
    $exe = Join-Path $game $ExeName
    $st = Get-ExeState $exe
    Write-Host "game folder: $game"
    Write-Host ("exe:         " + (Describe $st))
    $known = $KnownExes.ContainsKey($st.Hash)
    if (-not $known) {
        if (-not $Force) {
            Fail ("this StarWarsG.exe is not the Steam 64-bit version 1.121.859328 the patch was made for.`n" +
                  "The DLL checks every site and turns off what does not match, but nothing is promised.`n" +
                  "Run again with -Force to install anyway.")
        }
        Write-Host 'warning: unknown exe version, installing anyway (-Force)' -ForegroundColor Yellow
    }

    # 1. the DLL first, so a patched exe never points at a missing DLL
    $dst = Join-Path $game $DllName
    if ((Test-Path -LiteralPath $dst) -and ((Get-Sha256File $dst) -eq (Get-Sha256File $src))) {
        Write-Host 'dll:         already up to date'
    } else {
        if (Test-Path -LiteralPath $dst) {
            Copy-Item -LiteralPath $dst -Destination ($dst + '.prev') -Force
            Write-Host "dll:         previous one kept as $DllName.prev"
        }
        Copy-Item -LiteralPath $src -Destination $dst -Force
        Write-Host "dll:         copied $DllName"
    }

    # 2. the exe import
    if ($st.Name -ieq $NewName) {
        Write-Host "exe:         already points at $DllName"
    } else {
        $bak = $exe + $BackupSuffix
        Copy-Item -LiteralPath $exe -Destination $bak -Force   # the exe as it is now (unpatched) is the one to keep
        Write-Host "exe:         backed up as $ExeName$BackupSuffix"
        $oldName = $st.Name
        Set-ImportName $exe $st $NewName
        $st2 = Get-ExeState $exe
        if ($st2.Name -cne $NewName -or ($known -and $KnownExes[$st2.Hash] -ne 'patched')) {
            Fail "the exe did not verify after patching; restore it from $ExeName$BackupSuffix"
        }
        Write-Host "exe:         import renamed $oldName -> $NewName"
    }
    Write-Host ''
    Write-Host 'Done. Start the game as usual.' -ForegroundColor Green
    Write-Host ("The DLL log is " + (Join-Path $game 'zz_ability_buttons.log'))
    Write-Host 'After a Steam update or "Verify integrity of game files", run Install again.'
}

function Do-Uninstall {
    $game = Find-Game
    $exe = Join-Path $game $ExeName
    $st = Get-ExeState $exe
    Write-Host "game folder: $game"
    Write-Host ("exe:         " + (Describe $st))
    if ($st.Name -ieq $NewName) {
        Set-ImportName $exe $st $OldName
        $st2 = Get-ExeState $exe
        if ($st2.Name -cne $OldName) { Fail 'the exe did not verify after reverting' }
        $note = ''; if ($KnownExes[$st2.Hash] -eq 'stock') { $note = ' (matches stock)' }
        Write-Host "exe:         import restored to $OldName$note"
    } else { Write-Host "exe:         already imports $($st.Name)" }
    foreach ($n in @($DllName, "$DllName.prev")) {
        $p = Join-Path $game $n
        if (Test-Path -LiteralPath $p) { Remove-Item -LiteralPath $p -Force; Write-Host "dll:         removed $n" }
    }
    if (Test-Path -LiteralPath ($exe + $BackupSuffix)) { Write-Host "exe backup $ExeName$BackupSuffix left in place (delete it if you like)" }
    Write-Host ''
    Write-Host 'Done. The game runs without the engine patch now.' -ForegroundColor Green
}

try {
    if ($Status) { Do-Status } elseif ($Uninstall) { Do-Uninstall } else { Do-Install }
    exit 0
} catch [System.UnauthorizedAccessException], [System.IO.IOException] {
    Write-Host ("error: " + $_.Exception.Message) -ForegroundColor Red
    Write-Host 'Is the game still running? If the game is under Program Files, run the installer as administrator.' -ForegroundColor Red
    exit 1
} catch {
    Write-Host ("error: " + $_.Exception.Message) -ForegroundColor Red
    exit 1
}
