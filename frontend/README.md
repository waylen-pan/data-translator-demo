# 前端（数据翻译器）

技术栈：React 19 + Vite + TypeScript + Tailwind + shadcn/ui + TanStack Query。

## 本地开发

在 `data-translator-demo/frontend/` 目录执行：

```bash
npm install
npm run dev
```

说明：开发期 `vite.config.ts` 已配置 `"/api"` 代理到 `http://localhost:8000`，前端直接用相对路径请求即可。

## 质量检查

```bash
npm run lint
npm run build
```
