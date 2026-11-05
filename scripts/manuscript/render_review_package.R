args <- commandArgs(trailingOnly = TRUE)
output_dir <- if (length(args) >= 1) args[[1]] else "outputs/statistician-review"

root <- normalizePath(".", winslash = "/", mustWork = TRUE)
output_path <- if (grepl("^/", output_dir)) output_dir else file.path(root, output_dir)
output_dir <- normalizePath(
  output_path,
  winslash = "/",
  mustWork = FALSE
)
dir.create(output_dir, recursive = TRUE, showWarnings = FALSE)

run_citation_audit <- function(rendered_main = NULL, rendered_companion = NULL) {
  audit_args <- c(
    "run",
    "chicagohealthmap",
    "manuscript",
    "audit-citations",
    "--main", "manuscript/chicago_health_map_jama_health_forum_original_investigation.Rmd",
    "--companion", "notebooks/RMD_chm_paper_r_Ashley.Rmd",
    "--references", "manuscript/reference_verification.csv",
    "--claims", "manuscript/claim_evidence_map.csv",
    "--manifest", "config/manuscript/results_authorization.json"
  )
  if (!is.null(rendered_main)) {
    audit_args <- c(audit_args, "--rendered-main", shQuote(rendered_main))
  }
  if (!is.null(rendered_companion)) {
    audit_args <- c(audit_args, "--rendered-companion", shQuote(rendered_companion))
  }
  status <- system2("uv", audit_args, stdout = TRUE, stderr = TRUE)
  if (!is.null(attr(status, "status")) && attr(status, "status") != 0) {
    stop("Citation audit failed:\n", paste(status, collapse = "\n"))
  }
}

run_citation_audit()

render_file <- function(input, output_file, output_format = NULL) {
  rmarkdown::render(
    input = file.path(root, input),
    output_format = output_format,
    output_file = output_file,
    output_dir = output_dir,
    envir = new.env(parent = globalenv()),
    clean = TRUE,
    quiet = TRUE
  )
}

render_file(
  "manuscript/chicago_health_map_jama_health_forum_original_investigation.Rmd",
  "chicago_health_map_jama_health_forum_original_investigation.html"
)
render_file(
  "manuscript/chicago_health_map_jama_health_forum_original_investigation.Rmd",
  "chicago_health_map_jama_health_forum_original_investigation.md",
  rmarkdown::md_document(variant = "gfm")
)
render_file(
  "notebooks/RMD_chm_paper_r_Ashley.Rmd",
  "RMD_chm_paper_r_Ashley.html"
)

markdown_path <- file.path(
  output_dir,
  "chicago_health_map_jama_health_forum_original_investigation.md"
)
figure_name <- "figure_1_data_flow_coverage.png"
figure_source <- file.path(
  root,
  "outputs",
  "notebooks",
  "chicago_healthmap_master",
  figure_name
)
figure_target <- file.path(output_dir, figure_name)
stopifnot(file.copy(figure_source, figure_target, overwrite = TRUE))
markdown <- readLines(markdown_path, warn = FALSE)
markdown <- gsub(
  'src="[^"]*figure_1_data_flow_coverage\\.png"',
  paste0('src="', figure_name, '"'),
  markdown
)
writeLines(markdown, markdown_path, useBytes = TRUE)

local_image_targets <- regmatches(
  markdown,
  gregexpr('(?<=src=")[^"]+', markdown, perl = TRUE)
)
local_image_targets <- unlist(local_image_targets, use.names = FALSE)
local_image_targets <- local_image_targets[
  !grepl("^(?:https?:|data:)", local_image_targets)
]
stopifnot(
  all(file.exists(file.path(output_dir, local_image_targets)))
)

run_citation_audit(
  file.path(
    output_dir,
    "chicago_health_map_jama_health_forum_original_investigation.html"
  ),
  file.path(
    output_dir,
    "RMD_chm_paper_r_Ashley.html"
  )
)

expected <- file.path(
  output_dir,
  c(
    "chicago_health_map_jama_health_forum_original_investigation.html",
    "chicago_health_map_jama_health_forum_original_investigation.md",
    "figure_1_data_flow_coverage.png",
    "RMD_chm_paper_r_Ashley.html"
  )
)
stopifnot(all(file.exists(expected)), all(file.info(expected)$size > 0))
cat(paste(expected, collapse = "\n"), "\n")
