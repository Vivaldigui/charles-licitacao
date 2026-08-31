<#
.SYNOPSIS
    Limpeza da raiz do repositorio Charles - duplicatas do Google Drive,
    pastas fora da estrutura documentada e caches do Python.

.DESCRIPTION
    O script NAO apaga nada por padrao. Sem o parametro -Executar ele apenas
    simula e imprime o que faria (dry-run).

    Regras de seguranca embutidas:
      * So roda se a pasta parecer mesmo o repositorio Charles.
      * Faz backup completo de tudo que sera tocado ANTES de tocar.
      * Duplicatas "(1)" so sao apagadas quando o hash SHA256 bate com o
        arquivo original. Divergentes sao apenas RELATADAS, nunca apagadas.
      * Nao mexe em 08_processos_em_andamento/ nem em
        06_precedentes_camara/processos_2025/ - la o sufixo "(1)" costuma vir
        do proprio fornecedor e faz parte do processo.

    Observacao: este arquivo e mantido em ASCII puro de proposito. O Windows
    PowerShell 5.1 le scripts sem BOM como ANSI, e acentos em UTF-8 viram lixo.

.PARAMETER Raiz
    Caminho do repositorio. Padrao: duas pastas acima deste script.

.PARAMETER Backup
    Onde gravar o backup. Padrao: %USERPROFILE%\Charles_backup_limpeza_<carimbo>.
    Fica FORA do Google Drive de proposito, para nao voltar a sincronizar.

.PARAMETER Executar
    Sem este switch, nada e alterado. Com ele, as acoes sao aplicadas.

.EXAMPLE
    # 1) Simular (recomendado primeiro)
    powershell -ExecutionPolicy Bypass -File .\scripts\manutencao\limpar_raiz.ps1

.EXAMPLE
    # 2) Executar de verdade
    powershell -ExecutionPolicy Bypass -File .\scripts\manutencao\limpar_raiz.ps1 -Executar
#>

[CmdletBinding()]
param(
    [string] $Raiz,
    [string] $Backup,
    [switch] $Executar
)

$ErrorActionPreference = 'Stop'
$carimbo = Get-Date -Format 'yyyyMMdd_HHmmss'

# ---------------------------------------------------------------------------
# 0. Localizar e validar a raiz
# ---------------------------------------------------------------------------

if (-not $Raiz) {
    $Raiz = Split-Path -Parent (Split-Path -Parent $PSScriptRoot)
}
$Raiz = (Resolve-Path -LiteralPath $Raiz).Path

$assinaturas = @('CLAUDE.md', '05_minutas', '07_checklists', '00_indices')
foreach ($a in $assinaturas) {
    if (-not (Test-Path -LiteralPath (Join-Path $Raiz $a))) {
        throw "A pasta '$Raiz' nao parece ser o repositorio Charles (faltou '$a'). Abortado."
    }
}

if (-not $Backup) {
    $Backup = Join-Path $env:USERPROFILE "Charles_backup_limpeza_$carimbo"
}

$modo = if ($Executar) { 'EXECUCAO' } else { 'SIMULACAO (dry-run)' }

Write-Host ''
Write-Host '===========================================================' -ForegroundColor Cyan
Write-Host " Charles - limpeza da raiz            [$modo]" -ForegroundColor Cyan
Write-Host '===========================================================' -ForegroundColor Cyan
Write-Host " Repositorio : $Raiz"
Write-Host " Backup      : $Backup"
Write-Host ''

$acoes   = New-Object System.Collections.Generic.List[object]
$revisar = New-Object System.Collections.Generic.List[object]

function Add-Acao {
    param([string]$Tipo, [string]$Alvo, [string]$Detalhe)
    $acoes.Add([pscustomobject]@{ Tipo = $Tipo; Alvo = $Alvo; Detalhe = $Detalhe })
    $cor = switch ($Tipo) {
        'APAGAR'   { 'Yellow'  }
        'MOVER'    { 'Green'   }
        'ARQUIVAR' { 'Green'   }
        'QUARENT.' { 'Magenta' }
        'REINDEX'  { 'Cyan'    }
        default    { 'Gray'    }
    }
    Write-Host ("  [{0,-8}] {1}" -f $Tipo, $Alvo) -ForegroundColor $cor
    if ($Detalhe) { Write-Host ("             {0}" -f $Detalhe) -ForegroundColor DarkGray }
}

function Add-Revisao {
    param([string]$Arquivo, [string]$Motivo, [string]$Original)
    $comparacao = ''
    if ($Original -and (Test-Path -LiteralPath $Original)) {
        $iDup = Get-Item -LiteralPath $Arquivo -Force
        $iOri = Get-Item -LiteralPath $Original -Force
        $maisNovo = if ($iDup.LastWriteTime -gt $iOri.LastWriteTime) { 'a COPIA (1) e mais nova' }
                    elseif ($iOri.LastWriteTime -gt $iDup.LastWriteTime) { 'o ORIGINAL e mais novo' }
                    else { 'mesma data' }
        $comparacao = ("copia: {0:yyyy-MM-dd HH:mm} / {1} bytes | original: {2:yyyy-MM-dd HH:mm} / {3} bytes | {4}" -f `
                        $iDup.LastWriteTime, $iDup.Length, $iOri.LastWriteTime, $iOri.Length, $maisNovo)
    }
    $revisar.Add([pscustomobject]@{ Arquivo = $Arquivo; Motivo = $Motivo; Comparacao = $comparacao })
    Write-Host ("  [REVISAR ] {0}" -f $Arquivo) -ForegroundColor Magenta
    Write-Host ("             {0}" -f $Motivo)  -ForegroundColor DarkGray
    if ($comparacao) { Write-Host ("             {0}" -f $comparacao) -ForegroundColor DarkGray }
}

function Mover-Para-Quarentena {
    # Tira o arquivo do repositorio sem descartar: ele vai para uma pasta de
    # revisao dentro do backup, preservando o caminho relativo de origem.
    param([string]$Caminho, [string]$Motivo)
    $relativo = $Caminho.Substring($Raiz.Length).TrimStart('\')
    $destino  = Join-Path (Join-Path $Backup '_REVISAR_DUPLICATAS') $relativo
    Add-Acao -Tipo 'QUARENT.' -Alvo $Caminho -Detalhe $Motivo
    $revisar.Add([pscustomobject]@{
        Arquivo    = $Caminho
        Motivo     = $Motivo
        Comparacao = "movido para: $destino"
    })
    if ($Executar) {
        $pastaDst = Split-Path -Parent $destino
        if (-not (Test-Path -LiteralPath $pastaDst)) {
            New-Item -ItemType Directory -Path $pastaDst -Force | Out-Null
        }
        Move-Item -LiteralPath $Caminho -Destination $destino -Force
    }
}

function Copiar-ParaBackup {
    param([string]$Caminho)
    if (-not $Executar) { return }
    $relativo = $Caminho.Substring($Raiz.Length).TrimStart('\')
    $destino  = Join-Path $Backup $relativo
    $pastaDst = Split-Path -Parent $destino
    if (-not (Test-Path -LiteralPath $pastaDst)) {
        New-Item -ItemType Directory -Path $pastaDst -Force | Out-Null
    }
    Copy-Item -LiteralPath $Caminho -Destination $destino -Recurse -Force
}

function Remover-Item-Seguro {
    param([string]$Caminho)
    Copiar-ParaBackup -Caminho $Caminho
    if ($Executar) {
        Remove-Item -LiteralPath $Caminho -Recurse -Force
    }
}

function Hash-De {
    param([string]$Caminho)
    (Get-FileHash -LiteralPath $Caminho -Algorithm SHA256).Hash
}

if ($Executar) {
    New-Item -ItemType Directory -Path $Backup -Force | Out-Null
}

# ---------------------------------------------------------------------------
# 1. Duplicatas " (1)" criadas pela sincronizacao do Google Drive
# ---------------------------------------------------------------------------
# Escopo restrito de proposito: fora daqui, "(1)" costuma ser nome de origem
# (documento enviado por fornecedor), e apagar seria perda de prova processual.

Write-Host '--- 1. Duplicatas "(1)" do Google Drive -------------------' -ForegroundColor Cyan

$pastasRecursivas = @(
    (Join-Path $Raiz '00_indices'),
    (Join-Path $Raiz '05_minutas'),
    (Join-Path $Raiz 'scripts'),
    (Join-Path $Raiz '.pytest_cache')
)

$candidatas = New-Object System.Collections.Generic.List[System.IO.FileInfo]

# Raiz: apenas o primeiro nivel.
Get-ChildItem -LiteralPath $Raiz -File -Force |
    Where-Object { $_.Name -match '\(\d+\)' } |
    ForEach-Object { $candidatas.Add($_) }

# Demais pastas do escopo: recursivo.
foreach ($pasta in $pastasRecursivas) {
    if (Test-Path -LiteralPath $pasta) {
        Get-ChildItem -LiteralPath $pasta -File -Recurse -Force |
            Where-Object { $_.Name -match '\(\d+\)' } |
            ForEach-Object { $candidatas.Add($_) }
    }
}

if ($candidatas.Count -eq 0) { Write-Host '  nada encontrado' -ForegroundColor DarkGray }

# Arquivos que sao GERADOS por scripts/indexar_base.py: nao se escolhe entre
# copias, regenera-se. A duplicata sai e o indice e refeito no passo 6.
$geradosPeloIndexador = @('INDICE_GERAL.md', 'MAPA_POR_TEMA.md', 'BASE_INDEXADA.json')
$precisaReindexar = $false

foreach ($dup in $candidatas) {
    # "CLAUDE (1).md" -> "CLAUDE.md" ; ".env (1).example" -> ".env.example"
    $nomeOriginal = ($dup.Name -replace '\s*\(\d+\)', '')
    $original     = Join-Path $dup.DirectoryName $nomeOriginal

    if (-not (Test-Path -LiteralPath $original)) {
        Add-Revisao -Arquivo $dup.FullName -Motivo "Sem original correspondente ('$nomeOriginal'). Pode ser a unica copia - mantido."
        continue
    }

    if ((Hash-De $dup.FullName) -eq (Hash-De $original)) {
        Add-Acao -Tipo 'APAGAR' -Alvo $dup.FullName -Detalhe "identico a '$nomeOriginal' (SHA256 confere)"
        Remover-Item-Seguro -Caminho $dup.FullName
        continue
    }

    # --- Conteudo divergente: classificar antes de agir ---------------------

    $emMinutas   = $dup.FullName.StartsWith((Join-Path $Raiz '05_minutas'), 'OrdinalIgnoreCase')
    $ehDocx      = $dup.Extension -eq '.docx'
    $ehGerado    = $geradosPeloIndexador -contains $nomeOriginal
    $copiaMaisNova = (Get-Item -LiteralPath $dup.FullName -Force).LastWriteTime -gt `
                     (Get-Item -LiteralPath $original -Force).LastWriteTime

    if ($emMinutas -and $ehDocx) {
        # Minuta-mae: fonte travada da geracao de documentos. Nunca decidir por data.
        Mover-Para-Quarentena -Caminho $dup.FullName `
            -Motivo "Minuta-mae divergente de '$nomeOriginal'. Exige conferencia humana antes de descartar."
    }
    elseif ($ehGerado) {
        Add-Acao -Tipo 'APAGAR' -Alvo $dup.FullName -Detalhe "arquivo gerado por indexar_base.py - sera refeito"
        Remover-Item-Seguro -Caminho $dup.FullName
        $precisaReindexar = $true
    }
    elseif ($copiaMaisNova) {
        # A copia e mais recente que o original: pode conter edicao nao aplicada.
        Mover-Para-Quarentena -Caminho $dup.FullName `
            -Motivo "Mais recente que '$nomeOriginal'. Pode conter alteracao que nunca chegou ao original."
    }
    else {
        Add-Acao -Tipo 'APAGAR' -Alvo $dup.FullName -Detalhe "residuo antigo - '$nomeOriginal' e mais novo"
        Remover-Item-Seguro -Caminho $dup.FullName
    }
}

# ---------------------------------------------------------------------------
# 2. Duplicatas dentro de .git/  (sempre lixo de sincronizacao)
# ---------------------------------------------------------------------------
# Arquivos internos do Git nao tem versao "(1)" legitima: sao sempre restos
# de conflito do Drive e podem confundir ferramentas. Backup + remocao.

Write-Host ''
Write-Host '--- 2. Restos de sincronizacao dentro de .git/ ------------' -ForegroundColor Cyan

$pastaGit = Join-Path $Raiz '.git'
if (Test-Path -LiteralPath $pastaGit) {
    $lixoGit = @(Get-ChildItem -LiteralPath $pastaGit -File -Recurse -Force |
                 Where-Object { $_.Name -match '\(\d+\)' })
    if ($lixoGit.Count -gt 0) {
        foreach ($g in $lixoGit) {
            Add-Acao -Tipo 'APAGAR' -Alvo $g.FullName -Detalhe 'resto de conflito do Drive dentro do .git'
            Remover-Item-Seguro -Caminho $g.FullName
        }
    } else {
        Write-Host '  nada a fazer' -ForegroundColor DarkGray
    }
} else {
    Write-Host '  .git/ nao encontrado' -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 3. RELATORIO_IMPLEMENTACAO.md -> docs/
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '--- 3. Realocacao de documentos da raiz -------------------' -ForegroundColor Cyan

$relatorio = Join-Path $Raiz 'RELATORIO_IMPLEMENTACAO.md'
$pastaDocs = Join-Path $Raiz 'docs'
if (Test-Path -LiteralPath $relatorio) {
    $destino = Join-Path $pastaDocs 'RELATORIO_IMPLEMENTACAO.md'
    if (Test-Path -LiteralPath $destino) {
        Add-Revisao -Arquivo $relatorio -Motivo 'Ja existe docs\RELATORIO_IMPLEMENTACAO.md. Nao sobrescrevi.'
    }
    else {
        Add-Acao -Tipo 'MOVER' -Alvo $relatorio -Detalhe 'para docs\RELATORIO_IMPLEMENTACAO.md'
        Copiar-ParaBackup -Caminho $relatorio
        if ($Executar) {
            if (-not (Test-Path -LiteralPath $pastaDocs)) {
                New-Item -ItemType Directory -Path $pastaDocs -Force | Out-Null
            }
            Move-Item -LiteralPath $relatorio -Destination $destino
        }
    }
} else {
    Write-Host '  nada a fazer' -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 4. tmp/ -> arquivar em ZIP no backup e remover da raiz
# ---------------------------------------------------------------------------
# tmp/ guarda rascunhos de geracoes passadas (28/2026, 29/2026, VALID).
# Nao e descartado as cegas: vira um ZIP no backup antes de sumir da raiz.

Write-Host ''
Write-Host '--- 4. Pasta tmp/ -----------------------------------------' -ForegroundColor Cyan

$pastaTmp = Join-Path $Raiz 'tmp'
if (Test-Path -LiteralPath $pastaTmp) {
    $qtd = @(Get-ChildItem -LiteralPath $pastaTmp -Recurse -File -Force).Count
    $zip = Join-Path $Backup "tmp_$carimbo.zip"
    Add-Acao -Tipo 'ARQUIVAR' -Alvo $pastaTmp -Detalhe "$qtd arquivo(s) -> $zip, depois remover da raiz"
    if ($Executar) {
        Compress-Archive -Path (Join-Path $pastaTmp '*') -DestinationPath $zip -Force
        Remove-Item -LiteralPath $pastaTmp -Recurse -Force
    }
} else {
    Write-Host '  nada a fazer' -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 5. Caches do Python
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '--- 5. Caches do Python -----------------------------------' -ForegroundColor Cyan

$caches = New-Object System.Collections.Generic.List[string]
$pytestCache = Join-Path $Raiz '.pytest_cache'
if (Test-Path -LiteralPath $pytestCache) { $caches.Add($pytestCache) }
Get-ChildItem -LiteralPath $Raiz -Directory -Recurse -Force -Filter '__pycache__' -ErrorAction SilentlyContinue |
    ForEach-Object { $caches.Add($_.FullName) }

if ($caches.Count -gt 0) {
    foreach ($c in $caches) {
        if (Test-Path -LiteralPath $c) {
            Add-Acao -Tipo 'APAGAR' -Alvo $c -Detalhe 'cache regeneravel, ja ignorado pelo .gitignore'
            if ($Executar) { Remove-Item -LiteralPath $c -Recurse -Force }
        }
    }
} else {
    Write-Host '  nada a fazer' -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 6. Regerar os indices
# ---------------------------------------------------------------------------
# BASE_INDEXADA.json, INDICE_GERAL.md e MAPA_POR_TEMA.md sao derivados da base.
# Em vez de escolher entre copias divergentes, refaz-se a partir da fonte.

Write-Host ''
Write-Host '--- 6. Reindexacao da base --------------------------------' -ForegroundColor Cyan

if ($precisaReindexar) {
    $indexador = Join-Path $Raiz 'scripts\indexar_base.py'
    Add-Acao -Tipo 'REINDEX' -Alvo $indexador -Detalhe 'regera BASE_INDEXADA.json, INDICE_GERAL.md e MAPA_POR_TEMA.md'
    if ($Executar) {
        $python = Get-Command python -ErrorAction SilentlyContinue
        if (-not $python) { $python = Get-Command py -ErrorAction SilentlyContinue }
        if ($python) {
            Push-Location $Raiz
            try {
                & $python.Source $indexador
                if ($LASTEXITCODE -eq 0) {
                    Write-Host '  indices regerados com sucesso' -ForegroundColor Green
                } else {
                    Add-Revisao -Arquivo $indexador -Motivo "indexar_base.py terminou com codigo $LASTEXITCODE - rode manualmente e confira."
                }
            }
            catch {
                Add-Revisao -Arquivo $indexador -Motivo "Falha ao executar indexar_base.py: $($_.Exception.Message)"
            }
            finally { Pop-Location }
        }
        else {
            Add-Revisao -Arquivo $indexador -Motivo 'Python nao encontrado no PATH. Rode manualmente: python scripts/indexar_base.py'
        }
    }
} else {
    Write-Host '  nao necessaria' -ForegroundColor DarkGray
}

# ---------------------------------------------------------------------------
# 7. Relatorio final
# ---------------------------------------------------------------------------

Write-Host ''
Write-Host '===========================================================' -ForegroundColor Cyan
Write-Host " Acoes: $($acoes.Count)   |   Para revisao humana: $($revisar.Count)" -ForegroundColor Cyan
Write-Host '===========================================================' -ForegroundColor Cyan

$crase = [char]96          # ` -- montado assim para nao escapar dentro da string
$cc    = "$crase$crase"    # marcador de codigo do Markdown

$linhas = New-Object System.Collections.Generic.List[string]
$linhas.Add('# Relatorio de limpeza da raiz - Charles')
$linhas.Add('')
$linhas.Add("- Modo: $modo")
$linhas.Add("- Data: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')")
$linhas.Add("- Repositorio: $Raiz")
$linhas.Add("- Backup: $Backup")
$linhas.Add('')
$linhas.Add('## Acoes')
$linhas.Add('')
if ($acoes.Count -eq 0) { $linhas.Add('_Nenhuma._') }
foreach ($a in $acoes) {
    $linhas.Add('- **' + $a.Tipo + '** ' + $cc + $a.Alvo + $cc + ' - ' + $a.Detalhe)
}
$linhas.Add('')
$linhas.Add('## Pendente de decisao humana')
$linhas.Add('')
if ($revisar.Count -eq 0) { $linhas.Add('_Nenhum._') }
foreach ($r in $revisar) {
    $linhas.Add('- ' + $cc + $r.Arquivo + $cc + ' - ' + $r.Motivo)
    if ($r.Comparacao) { $linhas.Add('  - ' + $r.Comparacao) }
}

# O relatorio e sempre gravado, inclusive na simulacao, para conferencia.
$destinoRel = Join-Path $PSScriptRoot 'ULTIMO_RELATORIO.md'
$linhas | Set-Content -LiteralPath $destinoRel -Encoding UTF8

if ($revisar.Count -gt 0) {
    Write-Host ''
    Write-Host 'PENDENTE DE DECISAO HUMANA:' -ForegroundColor Magenta
    foreach ($r in $revisar) {
        Write-Host ("  - {0}" -f $r.Arquivo) -ForegroundColor Magenta
        Write-Host ("    {0}" -f $r.Motivo)  -ForegroundColor DarkGray
    }
}

Write-Host ''
Write-Host "Relatorio gravado em: $destinoRel" -ForegroundColor Green

if ($Executar) {
    Copy-Item -LiteralPath $destinoRel -Destination (Join-Path $Backup 'RELATORIO_LIMPEZA.md') -Force
    Write-Host "Backup completo em:   $Backup" -ForegroundColor Green
}
else {
    Write-Host 'Nada foi alterado. Para aplicar, rode de novo com -Executar.' -ForegroundColor Yellow
}

Write-Host ''
Write-Host 'IMPORTANTE - evitar que o problema volte:' -ForegroundColor Yellow
Write-Host '  O Google Drive esta sincronizando a pasta .git/, o que gera as copias'
Write-Host '  "(1)" e pode corromper o historico. No Google Drive para computador:'
Write-Host '  Configuracoes > Google Drive > pastas do meu computador > escolha a pasta'
Write-Host '  Charles > excluir da sincronizacao a subpasta .git (ou mantenha o'
Write-Host '  repositorio de trabalho fora do Drive e use o GitHub como sincronizacao).'
Write-Host ''
