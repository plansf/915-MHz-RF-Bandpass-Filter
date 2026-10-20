param([string]$KiCadBin = 'C:\Program Files\KiCad\9.0\bin', [switch]$SkipSimulation)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$cli = Join-Path $KiCadBin 'kicad-cli.exe'
$cadPython = Join-Path $KiCadBin 'python.exe'
function Run([string]$exe, [string[]]$arguments) {
    # Windows PowerShell 5 treats redirected native stderr as an ErrorRecord.
    # Preserve diagnostics but judge native commands by their actual exit code.
    $ErrorActionPreference = 'Continue'
    & $exe @arguments 2>&1 | ForEach-Object { "$_" }
    if ($LASTEXITCODE -ne 0) { throw "Failed ($LASTEXITCODE): $exe $arguments" }
}
Run $cadPython @('tools/build_kicad.py')
Run $cli @('sch','erc','--exit-code-violations','-o','hardware/erc.rpt','hardware/rf915.kicad_sch')
Run $cli @('pcb','drc','--exit-code-violations','--schematic-parity','-o','hardware/drc.rpt','hardware/rf915.kicad_pcb')
Run $cli @('pcb','drc','--exit-code-violations','-o','hardware/thru-drc.rpt','hardware/rf915-thru.kicad_pcb')
New-Item -ItemType Directory -Force results/cad | Out-Null
Run $cli @('sch','export','pdf','-o','results/cad/schematic.pdf','hardware/rf915.kicad_sch')
foreach ($name in @('rf915','rf915-thru')) {
    $board = "hardware/$name.kicad_pcb"
    $fab = "fabrication/$name/"
    New-Item -ItemType Directory -Force $fab | Out-Null
    Run $cli @('pcb','export','gerbers','-o',$fab,'-l','F.Cu,B.Cu,F.Paste,F.SilkS,F.Mask,B.Mask,Edge.Cuts',$board)
    Run $cli @('pcb','export','drill','-o',$fab,'--format','excellon','--generate-map','--map-format','pdf',$board)
    Run $cli @('pcb','export','pos','--format','csv','--units','mm','-o',"results/cad/$name-positions.csv",$board)
    Run $cli @('pcb','export','svg','-o',"results/cad/$name-top.svg",'--layers','F.Cu,F.SilkS,Edge.Cuts','--mode-single','--page-size-mode','2',$board)
    Run $cli @('pcb','export','svg','-o',"results/cad/$name-bottom.svg",'--layers','B.Cu,Edge.Cuts','--mode-single','--page-size-mode','2',$board)
    Compress-Archive -Path "$fab*" -DestinationPath "fabrication/$name-revA-gerbers.zip" -Force
}
Run 'python' @('-m','unittest','discover','-s','tests','-v')
if (-not $SkipSimulation) { Run 'python' @('rf915.py','simulate') }
Run 'python' @('rf915.py','analyze','results/simulation/nominal.s2p','--kind','simulation','--output','results/analysis-example','--reference','results/simulation/ideal.s2p')
Write-Output 'Digital prototype rebuilt; physical assembly and measurement remain.'
