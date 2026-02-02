export type PreviewTable = {
  type: "table"
  columns: string[]
  rows: Record<string, unknown>[]
}

export type PreviewJson = {
  type: "json"
  value: unknown
}

export type Preview = PreviewTable | PreviewJson

export type UploadFileResponse = {
  file_id: string
  detected_format: string
  field_candidates: string[]
  preview: Preview
}

export type CreateJobRequest = {
  file_id: string
  selected_fields: string[]
  row_limit: number
  mode: "add_columns" | "overwrite"
  target_lang: string
}

export type CreateJobResponse = {
  job_id: string
  status: string
}

export type JobStatusResponse = {
  job_id: string
  file_id: string
  status: string
  mode: string
  target_lang: string
  row_limit: number
  selected_fields: string[]
  progress_total: number
  progress_done: number
  progress_failed: number
  error_message: string
  download_url?: string | null
}

export type JobListItem = {
  job_id: string
  file_id: string
  filename: string
  status: string
  mode: string
  target_lang: string
  row_limit: number
  selected_fields: string[]
  progress_total: number
  progress_done: number
  progress_failed: number
  error_message: string
  download_url?: string | null
  created_at: string
  updated_at: string
}

export type JobListResponse = {
  jobs: JobListItem[]
  limit: number
  offset: number
}

