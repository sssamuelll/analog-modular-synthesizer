# export.ps1 — regenera DXF de corte y STL de render desde el modelo.
# Constitucion, Principio III: el budget corre ANTES y un export a medias
# sale con codigo de error, para que no se confunda con terminado.
$ErrorActionPreference = "Stop"
$repo = Split-Path (Split-Path $PSScriptRoot)
$scad = "C:\Program Files\OpenSCAD\openscad.exe"
if (-not (Test-Path $scad)) { $scad = (Get-Command openscad).Source }

python (Join-Path $repo "case/clearance_budget.py")
# El vocabulario de codigos es el de gates.py y hay que hablarlo entero:
# 0 = verde, 2 = HUECO declarado (trabajo a medias a proposito, NO fallo),
# cualquier otro = ROJO. Hasta el 2026-08-27 esto comparaba contra -ne 0, asi
# que un HUECO abortaba el export con el mensaje "budget en ROJO" -- mentira
# de estado, y en la direccion contraria a la que el codigo 2 existe.
$budgetHueco = ($LASTEXITCODE -eq 2)
if ($budgetHueco) { Write-Host "budget con HUECO declarado: se exporta, pero este export NO es apto para fabricar" }
elseif ($LASTEXITCODE -ne 0) { Write-Error "budget en ROJO: no se exporta nada"; exit 1 }

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
# LA COSTILLA VIAJA EN DOS FICHEROS desde el 2026-08-28, y hacen falta los dos.
# Fue desarrollo plano mientras era chapa plegada (con los alivios de las seis
# esquinas convexas, porque un corte no dice de donde doblar); al pasar a anillo
# fresado su DXF vuelve a ser el CONTORNO de la pieza -- silueta y ventana --,
# que es lo que se corta del blank.
# El segundo, costilla_dorso_2d, es lo que se fresa POR DETRAS: el contorno del
# rebaje donde asienta el acrilico y los centros de las roscas ciegas. Va aparte
# porque un DXF 2D no sabe decir "a 11 mm de profundidad" -- el mismo caso que
# kondor_cajeado_2d. Sin el, el anillo vuelve del taller SIN REBAJE, o sea con
# el acrilico sin sitio, y no se ve hasta desembalarlo.
# EL MARCO DE LA VENTANA (2026-08-29, noche) sustituye a las tres placas, el
# clip y la escuadra; el talon al miembro bajo; y la banda del miembro alto a
# los dos marcos de la trasera. Nueve DXF pasan a tres.
$piezas = "costado_2d","costilla_2d","costilla_dorso_2d","cupon_anillo_2d","bandeja_base_2d","tapa_valle_2d",
          "miembro_alto_2d","talon_2d","nariz_2d","marco_ventana_2d",
          "piel_trasera_2d",
          "kondor_cajeado_2d","lienzo_2d",
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
foreach ($m in "assembly_acrilico","assembly_aluminio","assembly_madera",
                "assembly_esqueleto","assembly_acero") {
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

# El 2 tiene que SOBREVIVIR hasta quien llama. La constitucion (punto III):
# «un script que deja el trabajo a medias sale con codigo de error,
# precisamente para que no se confunda con terminado». Si este guion saliera 0
# con el budget en HUECO, nadie aguas arriba podria distinguir una prevision
# de un export validado para taller. Se genera igual -- para mirar -- pero el
# codigo dice la verdad. Lo cazo codex en la revision del 2026-08-27.
if ($budgetHueco) {
  Write-Host "AVISO: hay un HUECO declarado en el budget; este export sirve para revisar, no para mandar al taller."
  exit 2
}
