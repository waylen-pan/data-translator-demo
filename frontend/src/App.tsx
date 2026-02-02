import { useEffect, useMemo, useState } from "react"
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { createJob, getJob, listJobs, uploadFile } from "@/lib/api"
import type { UploadFileResponse } from "@/lib/types"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import { Progress } from "@/components/ui/progress"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"

const LAST_JOB_ID_KEY = "dt_last_job_id"

function App() {
  const queryClient = useQueryClient()
  const [uploaded, setUploaded] = useState<UploadFileResponse | null>(null)
  const [selectedFields, setSelectedFields] = useState<string[]>([])
  const [customFields, setCustomFields] = useState<string[]>([])
  const [customFieldInput, setCustomFieldInput] = useState<string>("")
  const [rowLimit, setRowLimit] = useState<number>(50)
  const safeRowLimit = useMemo(() => {
    const v = Number(rowLimit)
    if (!Number.isFinite(v)) return 50
    return Math.max(1, Math.min(5000, Math.trunc(v)))
  }, [rowLimit])
  const [mode, setMode] = useState<"add_columns" | "overwrite">("add_columns")
  // 当前“选择查看”的任务 id：
  // - 优先读取 localStorage 的 last_job_id 作为初值
  // - 为空时由 jobs 列表自动决定一个默认展示项（见 effectiveJobId）
  const [jobId, setJobId] = useState<string>(() => {
    try {
      return localStorage.getItem(LAST_JOB_ID_KEY) ?? ""
    } catch {
      return ""
    }
  })

  const jobsQuery = useQuery({
    queryKey: ["jobs"],
    queryFn: async () => await listJobs({ limit: 20, offset: 0 }),
    refetchInterval: (q) => {
      const jobs = q.state.data?.jobs ?? []
      const hasRunning = jobs.some((j) => j.status === "pending" || j.status === "running")
      // 有进行中的任务时适当轮询列表，方便“关页后回来”看到最新状态
      return hasRunning ? 2000 : false
    },
  })

  const uploadMutation = useMutation({
    mutationFn: async (file: File) => await uploadFile(file),
    onSuccess: (data) => {
      setUploaded(data)
      setCustomFields([])
      setCustomFieldInput("")
      // 默认选中第一个候选字段/列，减少用户操作
      const first = data.field_candidates?.[0]
      setSelectedFields(first ? [first] : [])
    },
  })

  const createJobMutation = useMutation({
    mutationFn: async () => {
      if (!uploaded) throw new Error("请先上传文件")
      return await createJob({
        file_id: uploaded.file_id,
        selected_fields: selectedFields,
        row_limit: safeRowLimit,
        mode,
        target_lang: "zh-CN",
      })
    },
    onSuccess: (data) => {
      setJobId(data.job_id)
      try {
        localStorage.setItem(LAST_JOB_ID_KEY, data.job_id)
      } catch {
        // ignore
      }
      queryClient.invalidateQueries({ queryKey: ["jobs"] })
    },
  })

  // 说明：避免在 useEffect 里同步 setState（会触发 cascading renders，且 lint 不允许）。
  // 这里使用“派生值”的方式：当 jobId 为空时，从 jobs 列表里挑选一个默认展示项。
  const effectiveJobId = useMemo(() => {
    const jobs = jobsQuery.data?.jobs ?? []
    if (!jobs.length) return ""

    // 1) 如果 jobId 在列表里，直接使用（最符合用户预期）
    if (jobId && jobs.some((j) => j.job_id === jobId)) return jobId

    // 2) 否则优先展示“进行中”的任务，方便用户回来继续看进度
    const running = jobs.find((j) => j.status === "pending" || j.status === "running")
    return running?.job_id ?? jobs[0].job_id
  }, [jobId, jobsQuery.data?.jobs])

  // 把“当前实际展示的任务”写回 localStorage（不改 React state）
  useEffect(() => {
    if (!effectiveJobId) return
    try {
      localStorage.setItem(LAST_JOB_ID_KEY, effectiveJobId)
    } catch {
      // ignore
    }
  }, [effectiveJobId])

  const jobQuery = useQuery({
    queryKey: ["job", effectiveJobId],
    queryFn: async () => await getJob(effectiveJobId),
    enabled: Boolean(effectiveJobId),
    refetchInterval: (q) => {
      const status = q.state.data?.status
      if (status === "pending" || status === "running") return 1000
      return false
    },
  })

  const progressPct = useMemo(() => {
    const total = jobQuery.data?.progress_total ?? 0
    const done = jobQuery.data?.progress_done ?? 0
    if (!total) return 0
    return Math.max(0, Math.min(100, Math.round((done / total) * 100)))
  }, [jobQuery.data?.progress_done, jobQuery.data?.progress_total])

  const allFields = useMemo(() => {
    if (!uploaded) return []
    const merged = [...(uploaded.field_candidates ?? []), ...customFields]
    return Array.from(new Set(merged)).filter((x) => x.trim())
  }, [customFields, uploaded])

  const canStart = Boolean(uploaded) && selectedFields.length > 0 && !uploadMutation.isPending && !createJobMutation.isPending

  const formatTime = (s?: string | null) => {
    if (!s) return ""
    const d = new Date(s)
    if (!Number.isFinite(d.getTime())) return String(s)
    return d.toLocaleString()
  }

  return (
    <div className="min-h-svh bg-background text-foreground">
      <div className="mx-auto flex w-full max-w-5xl flex-col gap-6 px-4 py-10">
        <header className="flex flex-col gap-2">
          <h1 className="text-2xl font-semibold tracking-tight">数据翻译器</h1>
          <p className="text-sm text-muted-foreground">
            上传数据 → 自动识别格式 → 选择字段/列与行数 → 后台翻译 → 下载导出
          </p>
        </header>

        <Card>
          <CardHeader>
            <CardTitle>历史任务（同一浏览器可找回）</CardTitle>
            <CardDescription>任务归属绑定匿名会话 Cookie；换浏览器/无痕无法访问</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-3">
            {jobsQuery.isLoading ? <Badge variant="secondary">加载中</Badge> : null}
            {jobsQuery.isError ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {String(jobsQuery.error)}
              </div>
            ) : null}

            {jobsQuery.data?.jobs?.length ? (
              <div className="flex flex-col gap-2">
                {jobsQuery.data.jobs.map((j) => {
                  const active = j.job_id === effectiveJobId
                  const statusBadgeVariant =
                    j.status === "succeeded" ? "outline" : j.status === "failed" ? "destructive" : "secondary"
                  const progressText = j.progress_total ? `${j.progress_done}/${j.progress_total}` : ""
                  return (
                    <div key={j.job_id} className="flex flex-col gap-2 rounded-md border p-3 md:flex-row md:items-center">
                      <div className="flex flex-1 flex-col gap-1">
                        <div className="flex flex-wrap items-center gap-2 text-sm">
                          <Badge variant={statusBadgeVariant}>status: {j.status}</Badge>
                          {progressText ? <Badge variant="outline">{progressText}</Badge> : null}
                          {j.filename ? <Badge variant="outline">file: {j.filename}</Badge> : null}
                        </div>
                        <div className="text-xs text-muted-foreground">
                          job_id: {j.job_id} {j.created_at ? `· ${formatTime(j.created_at)}` : null}
                        </div>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          type="button"
                          size="sm"
                          variant={active ? "default" : "outline"}
                          onClick={() => {
                            setJobId(j.job_id)
                            try {
                              localStorage.setItem(LAST_JOB_ID_KEY, j.job_id)
                            } catch {
                              // ignore
                            }
                          }}
                        >
                          查看
                        </Button>
                        <Button
                          type="button"
                          size="sm"
                          variant="secondary"
                          onClick={() => jobsQuery.refetch()}
                          disabled={jobsQuery.isFetching}
                        >
                          刷新
                        </Button>
                      </div>
                    </div>
                  )
                })}
              </div>
            ) : jobsQuery.isLoading ? null : (
              <div className="text-sm text-muted-foreground">暂无历史任务（你创建的任务会出现在这里）。</div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>1) 上传数据</CardTitle>
            <CardDescription>支持 JSON / JSONL / CSV / XLSX</CardDescription>
          </CardHeader>
          <CardContent className="flex flex-col gap-4">
            <div className="flex items-center gap-3">
              <Input
                type="file"
                accept=".json,.jsonl,.csv,.xlsx"
                onChange={(e) => {
                  const f = e.target.files?.[0]
                  if (f) uploadMutation.mutate(f)
                  // 允许用户重复选择同一个文件触发 onChange（否则浏览器可能不会触发）
                  e.currentTarget.value = ""
                }}
              />
              {uploadMutation.isPending ? <Badge variant="secondary">上传中</Badge> : null}
              {uploaded ? <Badge variant="outline">格式: {uploaded.detected_format}</Badge> : null}
            </div>

            {uploadMutation.isError ? (
              <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                {String(uploadMutation.error)}
              </div>
            ) : null}
          </CardContent>
        </Card>

        {uploaded ? (
          <Card>
            <CardHeader>
              <CardTitle>2) 选择字段/列与翻译范围</CardTitle>
              <CardDescription>字段候选来自文件预览（前 20 行/条）</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-6">
              <div className="grid grid-cols-1 gap-4 md:grid-cols-3">
                <div className="flex flex-col gap-2">
                  <div className="text-sm font-medium">翻译前 N 行/条</div>
                  <Input
                    type="number"
                    min={1}
                    max={5000}
                    value={rowLimit}
                    onChange={(e) => setRowLimit(Number(e.target.value))}
                  />
                  <div className="flex flex-wrap gap-2">
                    {[50, 200, 500].map((n) => (
                      <Button
                        key={n}
                        type="button"
                        size="sm"
                        variant={safeRowLimit === n ? "default" : "outline"}
                        onClick={() => setRowLimit(n)}
                      >
                        {n}
                      </Button>
                    ))}
                  </div>
                  <div className="text-xs text-muted-foreground">建议 50 / 200 / 500 起步。</div>
                </div>

                <div className="flex flex-col gap-2">
                  <div className="text-sm font-medium">导出模式</div>
                  <Select value={mode} onValueChange={(v) => setMode(v as "add_columns" | "overwrite")}>
                    <SelectTrigger>
                      <SelectValue placeholder="选择导出模式" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="add_columns">新增 *_zh（推荐）</SelectItem>
                      <SelectItem value="overwrite">覆盖原值（仅译文）</SelectItem>
                    </SelectContent>
                  </Select>
                  <div className="text-xs text-muted-foreground">默认新增译文字段/列，保留原始数据。</div>
                </div>

                <div className="flex flex-col gap-2">
                  <div className="text-sm font-medium">目标语言</div>
                  <Input value="zh-CN（简体中文）" readOnly />
                </div>
              </div>

              <div className="flex flex-col gap-3">
                <div className="flex items-center justify-between">
                  <div className="text-sm font-medium">可选字段/列</div>
                  <div className="flex items-center gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setSelectedFields(allFields)}
                    >
                      全选
                    </Button>
                    <Button type="button" variant="outline" size="sm" onClick={() => setSelectedFields([])}>
                      清空
                    </Button>
                  </div>
                </div>

                <div className="flex flex-col gap-2 rounded-md border p-3">
                  <div className="text-xs text-muted-foreground">
                    JSON/JSONL 支持路径（例如 <code>nested.desc</code>、<code>items[].text</code>）。表格文件无需填写。
                  </div>
                  <div className="flex flex-col gap-2 md:flex-row">
                    <Input
                      placeholder="新增字段路径（可选）"
                      value={customFieldInput}
                      onChange={(e) => setCustomFieldInput(e.target.value)}
                    />
                    <Button
                      type="button"
                      variant="secondary"
                      onClick={() => {
                        const v = customFieldInput.trim()
                        if (!v) return
                        setCustomFields((prev) => Array.from(new Set([...prev, v])))
                        setSelectedFields((prev) => Array.from(new Set([...prev, v])))
                        setCustomFieldInput("")
                      }}
                    >
                      添加
                    </Button>
                  </div>
                </div>

                {allFields.length ? (
                  <div className="grid grid-cols-1 gap-2 md:grid-cols-2">
                    {allFields.map((f) => {
                      const checked = selectedFields.includes(f)
                      return (
                        <label key={f} className="flex items-center gap-2 rounded-md border p-2">
                          <Checkbox
                            checked={checked}
                            onCheckedChange={(v) => {
                              const isChecked = v === true
                              const next = isChecked
                                ? Array.from(new Set([...selectedFields, f]))
                                : selectedFields.filter((x) => x !== f)
                              setSelectedFields(next)
                            }}
                          />
                          <span className="text-sm">{f}</span>
                        </label>
                      )
                    })}
                  </div>
                ) : (
                  <div className="text-sm text-muted-foreground">
                    未识别到字段候选（可在上方手动添加字段路径后再开始翻译）。
                  </div>
                )}
              </div>

              <div className="flex items-center gap-3">
                <Button
                  onClick={() => {
                    createJobMutation.mutate()
                  }}
                  disabled={!canStart}
                >
                  开始翻译
                </Button>
                {createJobMutation.isPending ? <Badge variant="secondary">创建任务中</Badge> : null}
                {createJobMutation.isError ? (
                  <span className="text-sm text-destructive">{String(createJobMutation.error)}</span>
                ) : null}
                {!selectedFields.length ? (
                  <span className="text-sm text-destructive">请至少选择 1 个字段/列</span>
                ) : null}
              </div>

              <div className="flex flex-col gap-2">
                <div className="text-sm font-medium">预览</div>
                <PreviewView data={uploaded} />
              </div>
            </CardContent>
          </Card>
        ) : null}

        {effectiveJobId ? (
          <Card>
            <CardHeader>
              <CardTitle>3) 翻译进度</CardTitle>
              <CardDescription>任务会在后台执行；页面会自动轮询状态</CardDescription>
            </CardHeader>
            <CardContent className="flex flex-col gap-4">
              <div className="flex flex-wrap items-center gap-2 text-sm">
                <Badge variant="outline">job_id: {effectiveJobId}</Badge>
                <Badge variant="secondary">status: {jobQuery.data?.status ?? "loading"}</Badge>
                {jobQuery.data?.progress_total ? (
                  <Badge variant="outline">
                    {jobQuery.data.progress_done}/{jobQuery.data.progress_total}
                  </Badge>
                ) : null}
                {jobQuery.data?.progress_failed ? (
                  <Badge variant="destructive">failed: {jobQuery.data.progress_failed}</Badge>
                ) : null}
              </div>

              <div className="flex flex-col gap-2">
                <Progress value={progressPct} />
                <div className="text-xs text-muted-foreground">进度: {progressPct}%</div>
              </div>

              {jobQuery.data?.error_message ? (
                <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                  {jobQuery.data.error_message}
                </div>
              ) : null}

              {jobQuery.data?.download_url ? (
                <div className="flex items-center gap-3">
                  <Button asChild>
                    <a href={jobQuery.data.download_url} target="_blank" rel="noreferrer">
                      下载导出文件
                    </a>
                  </Button>
                  <span className="text-xs text-muted-foreground">{jobQuery.data.download_url}</span>
                </div>
              ) : null}
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  )
}

function PreviewView({ data }: { data: UploadFileResponse }) {
  if (data.preview.type === "table") {
    const cols = data.preview.columns.slice(0, 8)
    const rows = data.preview.rows.slice(0, 10)
    return (
      <div className="w-full overflow-auto rounded-md border">
        <table className="w-full text-sm">
          <thead className="bg-muted/40">
            <tr>
              {cols.map((c) => (
                <th key={c} className="whitespace-nowrap px-3 py-2 text-left font-medium">
                  {c}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {rows.map((r, idx) => (
              <tr key={idx} className="border-t">
                {cols.map((c) => (
                  <td key={c} className="max-w-[320px] truncate px-3 py-2 align-top">
                    {String(r[c] ?? "")}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    )
  }

  return (
    <pre className="max-h-96 overflow-auto rounded-md border bg-muted/20 p-3 text-xs">
      {JSON.stringify(data.preview.value, null, 2)}
    </pre>
  )
}

export default App
