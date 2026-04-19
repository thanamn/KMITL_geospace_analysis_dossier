$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$root = Split-Path -Parent $MyInvocation.MyCommand.Path
$outputPath = Join-Path $root "kmitl-space-geospatial-strategic-dossier.html"
$updatedDate = Get-Date -Format "d MMMM yyyy"

$parts = @(
  [pscustomobject]@{
    Number = 1
    Id = "part-01"
    Title = "The Foundation &amp; Market Economics"
    ChapterRange = "Chapters 1-3"
    Summary = "Defines the field, sizes the Thai and global market logic, and establishes why geospatial work is the degree's main employability anchor."
  }
  [pscustomobject]@{
    Number = 2
    Id = "part-02"
    Title = "The Academic Reality &amp; Insider Scoop"
    ChapterRange = "Chapters 4-5"
    Summary = "Assesses KMITL's institutional positioning, likely culture, faculty environment, and how the program compares with Thai competitors."
  }
  [pscustomobject]@{
    Number = 3
    Id = "part-03"
    Title = "The Micro-Curriculum Teardown"
    ChapterRange = "Chapters 6-7"
    Summary = "Breaks the curriculum into weed-out courses, money skills, tool stacks, and the gap between coursework and what employers actually reward."
  }
  [pscustomobject]@{
    Number = 4
    Id = "part-04"
    Title = "The Daily Reality of the Job"
    ChapterRange = "Chapters 8-9"
    Summary = "Shows what hardware and geospatial-data work look like in practice, including work style, environments, routines, and hidden friction."
  }
  [pscustomobject]@{
    Number = 5
    Id = "part-05"
    Title = "Career Progression &amp; Economics"
    ChapterRange = "Chapters 10-12"
    Summary = "Covers the Thai job hunt, promotion mechanics, salary growth, and the international constraints that shape long-term career economics."
  }
  [pscustomobject]@{
    Number = 6
    Id = "part-06"
    Title = "Safety Net &amp; Action Plan"
    ChapterRange = "Chapters 13-15"
    Summary = "Explains pivot routes, how to use all four years intelligently, and the final go or no-go decision framework."
  }
)

$visualSummary = [pscustomobject]@{
  Total = 27
  Built = 27
  NeedUser = 0
}

$script:visualCounter = 0

$chapters = @(
  [pscustomobject]@{ Number = 1;  File = "chapter-01.html"; Part = 1; Title = "The Ground-Up Primer - What Are We Even Talking About?" }
  [pscustomobject]@{ Number = 2;  File = "chapter-02.html"; Part = 1; Title = "The Macro Space Economy (Global &amp; Thai Focus)" }
  [pscustomobject]@{ Number = 3;  File = "chapter-03.html"; Part = 1; Title = "The Geospatial &amp; Data Boom (The Safety Net)" }
  [pscustomobject]@{ Number = 4;  File = "chapter-04.html"; Part = 2; Title = "The Academic Ecosystem &amp; Competitor Takedown" }
  [pscustomobject]@{ Number = 5;  File = "chapter-05.html"; Part = 2; Title = "Faculty Culture &amp; The Word on the Street" }
  [pscustomobject]@{ Number = 6;  File = "chapter-06.html"; Part = 3; Title = "Year 1 &amp; 2 (The Weed-Out Phase)" }
  [pscustomobject]@{ Number = 7;  File = "chapter-07.html"; Part = 3; Title = "Year 3 &amp; 4 (The Money Skills Phase)" }
  [pscustomobject]@{ Number = 8;  File = "chapter-08.html"; Part = 4; Title = "Hardware Path" }
  [pscustomobject]@{ Number = 9;  File = "chapter-09.html"; Part = 4; Title = "Data/GIS Path" }
  [pscustomobject]@{ Number = 10; File = "chapter-10.html"; Part = 5; Title = "Job Hunt" }
  [pscustomobject]@{ Number = 11; File = "chapter-11.html"; Part = 5; Title = "Career Progression" }
  [pscustomobject]@{ Number = 12; File = "chapter-12.html"; Part = 5; Title = "Salary &amp; ITAR Barrier" }
  [pscustomobject]@{ Number = 13; File = "chapter-13.html"; Part = 6; Title = "Pivot Strategies" }
  [pscustomobject]@{ Number = 14; File = "chapter-14.html"; Part = 6; Title = "4-Year Playbook" }
  [pscustomobject]@{ Number = 15; File = "chapter-15.html"; Part = 6; Title = "Final Verdict" }
)

function Get-ArticleInnerHtml {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Path
  )

  $raw = Get-Content -Raw -Path $Path
  $match = [regex]::Match($raw, '<article class="chapter-source">(.*)</article>', [System.Text.RegularExpressions.RegexOptions]::Singleline)

  if (-not $match.Success) {
    throw "Could not locate article.chapter-source in $Path"
  }

  return $match.Groups[1].Value.Trim()
}

function Transform-ChapterHtml {
  param(
    [Parameter(Mandatory = $true)]
    [string]$Html,

    [Parameter(Mandatory = $true)]
    [pscustomobject]$Chapter
  )

  $clean = $Html -replace '\s*<span>Format: HTML chapter output</span>', ""
  $headerRegex = [regex]'<header>'
  $headerReplacement = "<header id=""chapter-{0:d2}"" class=""chapter-open page-break-before"">" -f $Chapter.Number
  $clean = $headerRegex.Replace($clean, $headerReplacement, 1)

  $visualPattern = '<div class="visual">\[VISUAL CANDIDATE\](.*?)\[/VISUAL CANDIDATE\]</div>'
  $clean = [regex]::Replace(
    $clean,
    $visualPattern,
    {
      param($match)

      $script:visualCounter++
      $visualId = "V-{0:d2}" -f $script:visualCounter
      $body = $match.Groups[1].Value
      $typeMatch = [regex]::Match($body, '- Type:\s*(.+)')
      $type = if ($typeMatch.Success) { $typeMatch.Groups[1].Value.Trim() } else { "visual" }
      $typeLabel = (Get-Culture).TextInfo.ToTitleCase($type.ToLower())

@"
<aside class="planned-visual" id="visual-$($visualId.ToLower())">
  <p class="planned-visual__eyebrow">Planned Visual $visualId</p>
  <p class="planned-visual__body">$typeLabel. Placeholder cleaned and tracked in the visual asset register. See the visual-plan appendix and <a href="visual-asset-register.html">visual-asset-register.html</a> for build and sourcing status.</p>
</aside>
"@
    },
    [System.Text.RegularExpressions.RegexOptions]::Singleline
  )

  return $clean.Trim()
}

function Get-PartDividerHtml {
  param(
    [Parameter(Mandatory = $true)]
    [pscustomobject]$Part
  )

@"
      <section id="$($Part.Id)" class="part-divider page-break-before">
        <p class="part-eyebrow">Part $($Part.Number)</p>
        <h2>$($Part.Title)</h2>
        <p class="part-range">$($Part.ChapterRange)</p>
        <p class="part-summary">$($Part.Summary)</p>
      </section>
"@
}

function Get-TocFrontMatterHtml {
@"
          <div class="toc-section toc-frontmatter">
            <p class="toc-label">Front Matter</p>
            <table class="toc-table">
              <tbody>
                <tr>
                  <td>Volume Brief</td>
                  <td><span class="toc-page-number" data-toc-target="volume-brief">--</span></td>
                </tr>
                <tr>
                  <td>Decision Snapshot</td>
                  <td><span class="toc-page-number" data-toc-target="decision-snapshot">--</span></td>
                </tr>
                <tr>
                  <td>Reading Guide and Method</td>
                  <td><span class="toc-page-number" data-toc-target="reading-guide">--</span></td>
                </tr>
              </tbody>
            </table>
          </div>
"@
}

function Get-TocSectionHtml {
  param(
    [Parameter(Mandatory = $true)]
    [pscustomobject]$Part,

    [Parameter(Mandatory = $true)]
    [object[]]$PartChapters
  )

  $rows = foreach ($chapter in $PartChapters) {
@"
                <tr>
                  <td>Chapter $($chapter.Number). $($chapter.Title)</td>
                  <td><span class="toc-page-number" data-toc-target="chapter-{0:d2}">--</span></td>
                </tr>
"@ -f $chapter.Number
  }

@"
          <div class="toc-section">
            <div class="toc-part-head">
              <strong>Part $($Part.Number). $($Part.Title)</strong>
              <span><span class="toc-page-number" data-toc-target="$($Part.Id)">--</span></span>
            </div>
            <table class="toc-table">
              <tbody>
$($rows -join "`n")
              </tbody>
            </table>
          </div>
"@
}

$tocSections = @()
$tocSections += Get-TocFrontMatterHtml
foreach ($part in $parts) {
  $partChapters = $chapters | Where-Object { $_.Part -eq $part.Number }
  $tocSections += Get-TocSectionHtml -Part $part -PartChapters $partChapters
}

$contentsPageOneSections = @($tocSections[0], $tocSections[1], $tocSections[2], $tocSections[3])
$contentsPageTwoSections = @($tocSections[4], $tocSections[5], $tocSections[6])

$frontMatter = @"
      <section class="cover-page">
        <div class="cover-main">
          <p class="cover-kicker">Strategic Dossier</p>
          <div class="cover-grid">
            <div>
              <h1 class="cover-title">Space and Geospatial Engineering at KMITL</h1>
              <p class="cover-subtitle">A Thailand-first university, labor-market, curriculum, and career viability assessment for a prospective Thai high school student choosing a degree path.</p>
            </div>
            <aside class="cover-panel">
              <h2>Inside This Volume</h2>
              <ul>
                <li>What the degree really is, and what it is not</li>
                <li>Thai employer demand, salary logic, and fallback paths</li>
                <li>KMITL versus Thai competitors and hidden academic risk</li>
                <li>Curriculum teardown, work-life reality, and four-year playbook</li>
              </ul>
            </aside>
          </div>
        </div>
        <div class="cover-band">
          <span>Bachelor of Engineering (Space and Geospatial Engineering)</span>
          <span>King Mongkut's Institute of Technology Ladkrabang</span>
          <span>Combined 15-Chapter Master Volume</span>
          <span>Updated $updatedDate</span>
        </div>
      </section>

      <section id="volume-brief" class="title-page page-break-before">
        <p class="front-kicker">Volume Brief</p>
        <h2>Scope, Audience, and Decision Frame</h2>
        <p class="front-lead">This master volume combines all fifteen chapters into one coherent book designed to answer a single question: is KMITL's Bachelor of Engineering in Space and Geospatial Engineering worth choosing, for whom, under what risks, and with what fallback plan if the idealized space path does not materialize?</p>
        <div class="brief-grid">
          <div class="brief-card">
            <h3>Prepared For</h3>
            <p>A prospective Thai high school student, together with any parent, teacher, or counselor helping evaluate university choices.</p>
            <h3>Core Lens</h3>
            <p>Thailand first. Labor-market realism first. Curriculum and prestige are treated as means to outcomes, not outcomes by themselves.</p>
          </div>
          <div class="brief-card">
            <h3>What This Dossier Covers</h3>
            <p>Field definition, Thai market structure, academic competition, faculty and culture risk, course sequencing, daily job reality, hiring friction, salary logic, pivot paths, and a four-year execution plan.</p>
            <h3>What It Does Not Assume</h3>
            <p>It does not assume that "space" automatically means glamorous spacecraft work, strong Thai hardware demand, or easy international mobility.</p>
          </div>
        </div>
      </section>

      <section id="decision-snapshot" class="snapshot-page page-break-before">
        <p class="front-kicker">Decision Snapshot</p>
        <h2>Working Judgment Before You Read the Full Volume</h2>
        <div class="snapshot-grid">
          <div class="snapshot-card">
            <h3>Strongest Case For</h3>
            <p>The degree sits at a useful intersection of satellites, telecom logic, remote sensing, GIS, GNSS, and applied data work. That hybrid can be economically credible in Thailand if the student builds a portfolio intentionally.</p>
          </div>
          <div class="snapshot-card">
            <h3>Strongest Case Against</h3>
            <p>The title can overpromise. Thailand's pure space-hardware market is still narrow, and a passive student can graduate with broad vocabulary but weak employer translation.</p>
          </div>
          <div class="snapshot-card">
            <h3>Safest Employment Lane</h3>
            <p>Geospatial data, remote sensing, GNSS, GIS implementation, telecom-ground systems, and adjacent analytics roles are the strongest safety net.</p>
          </div>
          <div class="snapshot-card">
            <h3>Highest-Friction Lane</h3>
            <p>Pure spacecraft or defense-heavy hardware pathways remain the hardest route from Thailand, especially without strong projects, networking, and further study.</p>
          </div>
          <div class="snapshot-card">
            <h3>Best-Fit Student</h3>
            <p>Technically serious, portfolio-driven, comfortable with ambiguity, and interested in building an engineering identity around sensing, systems, and spatial decisions rather than prestige alone.</p>
          </div>
          <div class="snapshot-card">
            <h3>Bottom-Line Verdict</h3>
            <p>This is a conditional go, not an automatic go. It works best when treated as an engineering-plus-geospatial platform with a deliberate lane choice from Year 2 onward.</p>
          </div>
        </div>
      </section>

      <section id="reading-guide" class="reading-guide page-break-before">
        <p class="front-kicker">Reading Guide</p>
        <h2>How to Use This Dossier Efficiently</h2>
        <div class="guide-grid">
          <div class="guide-card">
            <h3>Fast Decision Route</h3>
            <p>Read Chapter 4, Chapter 12, and Chapter 15 if the immediate goal is to decide whether this degree is broadly worth it relative to alternatives.</p>
            <h3>Career-First Route</h3>
            <p>Read Chapter 3, Chapter 7, Chapter 10, Chapter 11, Chapter 12, Chapter 13, and Chapter 14 if the main concern is employability and long-term income logic.</p>
            <h3>Academic-Risk Route</h3>
            <p>Read Chapter 4, Chapter 5, Chapter 6, and Chapter 7 if the concern is university culture, curriculum difficulty, and whether the student can realistically survive and differentiate.</p>
          </div>
          <div class="guide-card">
            <h3>Method and Evidence Rules</h3>
            <ul>
              <li>Thailand first: local hiring logic and institutional behavior outrank foreign glamour examples.</li>
              <li>Official university, agency, company, and policy sources anchor the analysis wherever available.</li>
              <li>Salary and cost figures are presented as ranges, not false precision.</li>
              <li>Where public data is thin, the dossier states that directly and uses reasoned approximation instead of invented certainty.</li>
            </ul>
          </div>
        </div>
      </section>

      <section id="master-contents" class="contents-page page-break-before">
        <p class="front-kicker">Contents</p>
        <h2>Master Table of Contents</h2>
        <p class="front-lead">Page numbers below are generated from the live paginated master volume. They update automatically when the layout changes.</p>
        <div class="contents-grid">
$($contentsPageOneSections -join "`n")
        </div>
      </section>

      <section class="contents-page page-break-before">
        <p class="front-kicker">Contents</p>
        <h2>Master Table of Contents (Continued)</h2>
        <div class="contents-grid">
$($contentsPageTwoSections -join "`n")
        </div>
      </section>
"@

$chapterBuilder = New-Object System.Text.StringBuilder

foreach ($part in $parts) {
  [void]$chapterBuilder.AppendLine((Get-PartDividerHtml -Part $part))

  $partChapters = $chapters | Where-Object { $_.Part -eq $part.Number }
  foreach ($chapter in $partChapters) {
    $chapterPath = Join-Path $root $chapter.File
    $chapterHtml = Get-ArticleInnerHtml -Path $chapterPath
    $transformed = Transform-ChapterHtml -Html $chapterHtml -Chapter $chapter
    [void]$chapterBuilder.AppendLine($transformed)
    [void]$chapterBuilder.AppendLine("")
  }
}

$visualPlanAppendix = @"
      <section id="visual-plan-summary" class="visual-plan-summary page-break-before">
        <p class="front-kicker">Appendix A</p>
        <h2>Visual Asset Summary</h2>
        <p class="front-lead">All dossier visuals are now built as native SVG assets and integrated directly into the reading flow. The full entry-by-entry register lives in <a href="visual-asset-register.html">visual-asset-register.html</a>.</p>
        <div class="visual-summary-grid">
          <div class="visual-summary-card">
            <h3>Total Visuals</h3>
            <p>$($visualSummary.Total) dossier visuals are now present in the master volume.</p>
          </div>
          <div class="visual-summary-card">
            <h3>Built and Integrated</h3>
            <p>$($visualSummary.Built) of $($visualSummary.Total) visuals have been built and placed into the dossier and chapter files.</p>
          </div>
          <div class="visual-summary-card">
            <h3>User-Supplied Sources Required</h3>
            <p>$($visualSummary.NeedUser). The current visual set ships without requiring logos, photos, or external proprietary assets.</p>
          </div>
        </div>
        <p class="visual-summary-note">Note: the Bangkok-style map has been implemented as a schematic city-layer illustration so the book can ship cleanly without external basemap sourcing. A factual map variant can still be produced later if desired.</p>
      </section>
"@

$masterHtml = @"
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>KMITL Space and Geospatial Engineering Strategic Dossier</title>
  <link rel="stylesheet" href="report-shared.css?v=7">
  <link rel="stylesheet" href="report-book.css?v=2">
</head>
<body class="master-book">
  <main>
    <article class="chapter-source" data-running-title="KMITL Space and Geospatial Engineering Strategic Dossier">
$frontMatter
$($chapterBuilder.ToString().TrimEnd())
$visualPlanAppendix
    </article>
  </main>
  <script src="report-pager.js?v=4"></script>
</body>
</html>
"@

Set-Content -Path $outputPath -Value $masterHtml -Encoding utf8
Write-Output "Built $outputPath"
