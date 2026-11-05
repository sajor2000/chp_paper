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

expected <- file.path(
  output_dir,
  c(
    "chicago_health_map_jama_health_forum_original_investigation.html",
    "chicago_health_map_jama_health_forum_original_investigation.md",
    "RMD_chm_paper_r_Ashley.html"
  )
)
stopifnot(all(file.exists(expected)), all(file.info(expected)$size > 0))
cat(paste(expected, collapse = "\n"), "\n")
