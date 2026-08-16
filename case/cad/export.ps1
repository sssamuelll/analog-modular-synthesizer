# export.ps1 — regenera DXF de corte y STL de render desde el modelo.
# Constitucion, Principio III: el budget corre ANTES y un export a medias
# sale con codigo de error, para que no se confunda con terminado.
$ErrorActionPreference = "Stop"
$repo = Split-Path (Split-Path $PSScriptRoot)
$scad = "C:\Program Files\OpenSCAD\openscad.exe"
if (-not (Test-Path $scad)) { $scad = (Get-Command openscad).Source }

python (Join-Path $repo "case/clearance_budget.py")
if ($LASTEXITCODE -ne 0) { Write-Error "budget en ROJO: no se exporta nada"; exit 1 }

$plans = Join-Path $repo "case/plans"
$build = Join-Path $repo "case/renders/build"
New-Item -ItemType Directory -Force $plans, $build | Out-Null

$piezas = "costado_2d","bandeja_base_2d","bandeja_entrepiso_2d",
          "zocalo_2d","piel_inferior_2d","piel_superior_2d","lienzo_2d"
$fallos = 0
foreach ($p in $piezas) {
  $out = Join-Path $plans "$p.dxf"
  # ojo: comillas escapadas — PowerShell 5.1 despoja las internas sin \ (fallo silencioso, verificado en Task 3)
  # ojo: OpenSCAD 2021.01 requiere forward slashes en rutas de output
  & $scad -o ($out.Replace('\', '/')) -D ('PART=\"' + $p + '\"') (Join-Path $PSScriptRoot "sam17_case.scad") | Out-Null
  if (-not (Test-Path $out) -or (Get-Item $out).Length -lt 1000) {
    Write-Warning "FALLO: $p"; $fallos++
  }
}
$coupon_out = (Join-Path $plans "coupon.dxf").Replace('\', '/')
& $scad -o $coupon_out (Join-Path $PSScriptRoot "coupon.scad") | Out-Null
if (-not (Test-Path $coupon_out)) { $fallos++ }
foreach ($m in "assembly_acrilico","assembly_aluminio") {
  $out = Join-Path $build "$m.stl"
  & $scad -o ($out.Replace('\', '/')) -D ('PART=\"' + $m + '\"') (Join-Path $PSScriptRoot "sam17_case.scad") | Out-Null
  if (-not (Test-Path $out) -or (Get-Item $out).Length -lt 10000) {
    Write-Warning "FALLO: $m"; $fallos++
  }
}
if ($fallos -gt 0) { Write-Error "$fallos exports fallidos"; exit 1 }

# puerta de relectura: validar lo que el laser va a ver, no lo que dibujamos
python (Join-Path $repo "case/check_dxf.py")
if ($LASTEXITCODE -ne 0) { Write-Error "check_dxf en ROJO: no se manda a cortar"; exit 1 }
Write-Output "export completo: $($piezas.Count + 3) artefactos regenerados y releidos"
