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

# limpieza previa: no reutilizar artefactos stale (false-pass risk)
Remove-Item (Join-Path $plans "*.dxf") -ErrorAction SilentlyContinue
Remove-Item (Join-Path $build "*.stl") -ErrorAction SilentlyContinue

# Las tres ultimas son de ACERO y van a otro taller (corte + plegado), no al
# de acrilico. Salen igual de aqui para que hereden la puerta de relectura y no
# vivan en un flujo aparte que nadie corre.
# kondor_cajeado_2d NO es una pieza de corte: es el CAJEADO CIEGO del relieve
# de la trasera, que no se recorta en piel_trasera_2d porque no atraviesa. Va
# en su propio fichero porque un DXF 2D no sabe decir "a 4 mm de profundidad"
# -- el mismo caso del chasis, cuyo corte no dice de donde doblar. Sin este
# fichero la trasera vuelve del taller SIN LA MARCA y nadie se entera hasta
# desembalarla. Lo vigila guarda_kondor() en check_dxf.
# costilla_2d NO SE EXPORTA todavia, y es deliberado: al pasar a chapa plegada
# el 2026-08-26 su DXF dejo de ser el contorno de la pieza y tiene que ser el
# DESARROLLO PLANO, con los cortes de alivio de las seis esquinas convexas --
# el mismo caso del chasis, cuyo corte no dice de donde doblar. Exportar el
# contorno mandaria a cortar una pieza que al plegarse no da la cota. Lo
# declara SIN_DXF en check_dxf.py.
$piezas = "costado_2d","costilla_2d","bandeja_base_2d","tapa_valle_2d",
          "remate_sup_2d","piel_trasera_2d","kondor_cajeado_2d","lienzo_2d",
          "chasis_cuerpo_2d","chasis_tapa_2d","chasis_refuerzo_2d"
# Piso de tamano del DXF. Es un SMOKE TEST -- "OpenSCAD escribio algo" --, no una
# verificacion: de eso se encarga check_dxf.py, que relee cada fichero con ezdxf
# y comprueba entidades y envolvente. Fue 1000 y era un piso a ojo: el dia que la
# pestana perdio sus cinco M3 quedo en un rectangulo redondeado de 378 bytes,
# perfectamente valido, y el gate lo dio por fallido. Un DXF degenerado de
# OpenSCAD no llega ni a esto -- si no hay geometria, ni siquiera escribe el
# fichero, que es lo que atrapa el Test-Path de al lado.
$dxf_min = 200
$fallos = 0
foreach ($p in $piezas) {
  $out = Join-Path $plans "$p.dxf"
  # ojo: comillas escapadas — PowerShell 5.1 despoja las internas sin \ (fallo silencioso, verificado en Task 3)
  # ojo: OpenSCAD 2021.01 requiere forward slashes en rutas de output
  & $scad -o ($out.Replace('\', '/')) -D ('PART=\"' + $p + '\"') (Join-Path $PSScriptRoot "sam17_case.scad") | Out-Null
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $out) -or (Get-Item $out).Length -lt $dxf_min) {
    Write-Warning "FALLO: $p"; $fallos++
  }
}
$coupon_out = Join-Path $plans "coupon.dxf"
& $scad -o ($coupon_out.Replace('\', '/')) (Join-Path $PSScriptRoot "coupon.scad") | Out-Null
if ($LASTEXITCODE -ne 0 -or -not (Test-Path $coupon_out) -or (Get-Item $coupon_out).Length -lt $dxf_min) {
  Write-Warning "FALLO: coupon"; $fallos++
}
foreach ($m in "assembly_acrilico","assembly_aluminio","assembly_madera") {
  $out = Join-Path $build "$m.stl"
  & $scad -o ($out.Replace('\', '/')) -D ('PART=\"' + $m + '\"') (Join-Path $PSScriptRoot "sam17_case.scad") | Out-Null
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $out) -or (Get-Item $out).Length -lt 10000) {
    Write-Warning "FALLO: $m"; $fallos++
  }
}

# Vistas del chasis de acero. Es la unica pieza cuyo INTERIOR es el diseno, y no
# se ve en ningun otro entregable: el DXF es plano y en el render del case queda
# detras de los paneles (probado, ver la nota en render.py). Van a build/ y no se
# versionan, igual que los STL -- son de viewport y se regeneran en un segundo.
foreach ($v in "chasis_abierto=32,0,0", "chasis_cerrado=62,0,28") {
  $nombre, $cam = $v.Split("=")
  $out = Join-Path $build "vista_$nombre.png"
  & $scad -o ($out.Replace('\', '/')) --imgsize=1500,950 --viewall --autocenter --colorscheme=Tomorrow --camera="0,0,0,$cam,0" -D ('PART=\"' + $nombre + '\"') (Join-Path $PSScriptRoot "sam17_case.scad") | Out-Null
  if ($LASTEXITCODE -ne 0 -or -not (Test-Path $out) -or (Get-Item $out).Length -lt 5000) {
    Write-Warning "FALLO: vista $nombre"; $fallos++
  }
}
if ($fallos -gt 0) { Write-Error "$fallos exports fallidos"; exit 1 }

# puerta de relectura: validar lo que el laser va a ver, no lo que dibujamos
python (Join-Path $repo "case/check_dxf.py")
if ($LASTEXITCODE -ne 0) { Write-Error "check_dxf en ROJO: no se manda a cortar"; exit 1 }

# El plano de plegado. El DXF NO es entregable completo para una chapa doblada:
# lleva el corte y no dice de donde doblar. Este si se versiona.
python (Join-Path $repo "case/renders/plano_chasis.py")
if ($LASTEXITCODE -ne 0) { Write-Error "plano de plegado en ROJO"; exit 1 }
Write-Output "export completo: $($piezas.Count + 6) artefactos regenerados y releidos"
