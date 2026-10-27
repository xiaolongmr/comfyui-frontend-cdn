# ComfyUI Frontend CDN Assets

ComfyUI 前端构建产物（`assets/` 目录），用于通过 jsDelivr 加速访问。

- 来源：`comfyui_frontend_package/static/assets`
- 已排除 `*.js.map`（source map，浏览器正常不请求，约 63 MB）
- 文件名自带内容哈希，内容不变则文件名不变，可长期缓存
- ComfyUI 升级前端版本后需重新上传并更新 commit 引用

jsDelivr 用法：

```
https://cdn.jsdelivr.net/gh/xiaolongmr/comfyui-frontend-cdn@<commit>/assets/<file>
```
