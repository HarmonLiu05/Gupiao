# Repository Guidelines

## 项目结构与模块组织

当前仓库还很轻量。后续添加代码时，从仓库根目录保持清晰结构：

- `src/` 放应用或库源码。
- `tests/` 放自动化测试，并尽量镜像 `src/` 的结构。
- `assets/` 放图片、fixtures、样例数据或静态资源。
- `docs/` 放较长的设计说明、API 参考或贡献文档。
- `plan/` 放给 Codex 执行窗口使用的中文实施计划。
- 根目录的 `package.json`、`pyproject.toml`、`Makefile`、`.editorconfig` 等文件用于定义实际工具链。

不要把生成物、本地缓存或大体积二进制文件放进源码目录。

## 构建、测试与开发命令

当前还没有提交具体构建系统。添加工具链后，把准确命令写入相关文档，并优先使用常见命名：

- `npm install` / `pip install -e .`：安装依赖。
- `npm run dev` / `python -m <module>`：本地运行。
- `npm test` / `pytest`：运行测试。
- `npm run lint` / `ruff check .`：运行静态检查。
- `npm run build` / `python -m build`：生成构建产物。

所有命令应能从仓库根目录稳定执行。

## 编码风格与命名约定

遵循项目已配置的 formatter 和 linter。若尚未配置，保持缩进一致、命名清晰、模块职责单一。Python 文件和函数使用 `snake_case`，JavaScript 变量和函数使用 `camelCase`，类和 React 组件使用 `PascalCase`。

文件名应体现主要职责，例如 `user_service.py`、`apiClient.ts`、`LoginForm.tsx`。

## 测试规范

测试放在 `tests/` 下，测试名称应描述行为。根据语言使用 `test_<feature>.py`、`<feature>.test.ts` 或 `<Component>.test.tsx`。每个新功能或 bug 修复都应覆盖正常路径，并至少包含一个失败或边界场景。

## Commit 与 Pull Request 规范

当前目录不是 Git 仓库，因此没有可读取的本地提交惯例。提交信息使用简洁祈使句，例如 `Add parser validation` 或 `Fix login redirect`。

PR 应包含简短摘要、变更原因、已运行的验证命令、相关 issue 链接；涉及 UI 时附截图或录屏。

## 安全与配置

不要提交 secrets、credentials、`.env` 文件或机器特定路径。需要配置时，提交 `.env.example`，并在 `docs/`、`plan/` 或本指南中说明必需变量。
