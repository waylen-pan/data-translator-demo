import type { CreateJobRequest, CreateJobResponse, JobListResponse, JobStatusResponse, UploadFileResponse } from "@/lib/types"

async function apiFetch<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(path, init)
  if (!resp.ok) {
    // 统一提取后端错误信息（优先解析 FastAPI 的 {"detail": "..."}）
    const contentType = resp.headers.get("content-type") ?? ""
    let message = ""
    if (contentType.includes("application/json")) {
      try {
        const data = (await resp.json()) as unknown as { detail?: unknown }
        if (typeof data?.detail === "string") message = data.detail
        else if (data?.detail != null) message = JSON.stringify(data.detail)
        else message = JSON.stringify(data)
      } catch {
        // ignore
      }
    }
    if (!message) {
      try {
        message = await resp.text()
      } catch {
        message = ""
      }
    }
    message = message.trim()
    throw new Error(message || `请求失败: ${resp.status}`)
  }
  return (await resp.json()) as T
}

export async function uploadFile(file: File): Promise<UploadFileResponse> {
  const fd = new FormData()
  fd.append("file", file)
  return await apiFetch<UploadFileResponse>("/api/v1/files/upload", {
    method: "POST",
    body: fd,
  })
}

export async function createJob(req: CreateJobRequest): Promise<CreateJobResponse> {
  return await apiFetch<CreateJobResponse>("/api/v1/jobs", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(req),
  })
}

export async function getJob(jobId: string): Promise<JobStatusResponse> {
  return await apiFetch<JobStatusResponse>(`/api/v1/jobs/${jobId}`, {
    method: "GET",
  })
}

export async function listJobs(params?: { limit?: number; offset?: number }): Promise<JobListResponse> {
  const limit = params?.limit
  const offset = params?.offset
  const qs = new URLSearchParams()
  if (typeof limit === "number") qs.set("limit", String(limit))
  if (typeof offset === "number") qs.set("offset", String(offset))
  const suffix = qs.toString() ? `?${qs.toString()}` : ""
  return await apiFetch<JobListResponse>(`/api/v1/jobs${suffix}`, { method: "GET" })
}

