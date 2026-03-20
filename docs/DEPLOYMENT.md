# Deployment Guide / 部署手册

## 1. Goal / 目标

This repository provides a **semi-automatic deployment** flow for:

- Jarvis Memory
- True Recall
- OpenClaw workspace integration

本仓库提供一套**半自动部署**流程，用来在已经安装好的 OpenClaw 主机上部署：

- Jarvis Memory
- True Recall
- OpenClaw workspace 集成层

The design goal is:

- install OpenClaw first
- run one bootstrap command
- let the script complete all safe automatic steps
- pause only when human input is truly needed
- keep the deployment reproducible from GitHub

设计目标是：

- 先安装 OpenClaw
- 再执行一条 bootstrap 命令
- 能自动完成的步骤全部自动完成
- 只有必须由人工提供的信息才停下来
- 整套部署以后都以 GitHub 为准

## 2. What Is Automatic / 自动完成部分

The bootstrap script automatically handles:

- host dependency installation
- Docker validation and startup
- Redis + Qdrant startup
- Ollama validation
- Ollama model check and pull
- workspace file sync
- `.memory_env` generation
- timezone configuration
- cron installation
- final audit

`bootstrap/bootstrap.sh` 会自动完成：

- 宿主机依赖安装
- Docker 检查与启动
- Redis + Qdrant 启动
- Ollama 检查
- Ollama 模型检查和拉取
- workspace 文件同步
- `.memory_env` 生成
- 时区配置
- cron 安装
- 最终审计

## 3. What Still Needs Human Help / 仍需人工协助部分

Human input is only needed for values the script cannot safely invent.

只有脚本无法安全猜测的值，才需要人工输入。

### Required manual inputs / 必填人工输入

- `USER_ID`
  - Example: `tars`
  - Used as the memory owner id in Redis and Qdrant.
  - 用作 Redis 和 Qdrant 中的记忆归属标识。

- `TIMEZONE`
  - Default: `America/Los_Angeles`
  - Used by cron scheduling.
  - 用于 cron 调度的时区基准。

### Optional manual decisions / 可选人工决定

- whether to keep the default schedule
- whether to change the OpenClaw user from `openclaw`
- whether to use a different curator model

可选的人为决定包括：

- 是否保留默认定时
- 是否修改默认 OpenClaw 用户 `openclaw`
- 是否更换 curator 模型

## 4. Standard New-Server Flow / 新服务器标准流程

### Step A. Install OpenClaw first / 先安装 OpenClaw

The bootstrap repo does **not** install OpenClaw itself.

本仓库**不负责**安装 OpenClaw 本体。

You should first make sure these paths already exist:

你应先确认下面路径已经存在：

```bash
/home/openclaw/.openclaw
/home/openclaw/.openclaw/agents/main/sessions
```

### Step B. Clone this GitHub repo / 拉取本仓库

```bash
git clone https://github.com/godlovestome/jarvismemory.git
cd jarvismemory
```

### Step C. Run bootstrap / 执行 bootstrap

```bash
sudo bash bootstrap/bootstrap.sh
```

If `USER_ID` or `TIMEZONE` was not passed in, the script will prompt for them.

如果没有提前传入 `USER_ID` 或 `TIMEZONE`，脚本会在运行中提示输入。

Example:

```bash
sudo USER_ID=tars TIMEZONE=America/Los_Angeles bash bootstrap/bootstrap.sh
```

示例：

```bash
sudo USER_ID=tars TIMEZONE=America/Los_Angeles bash bootstrap/bootstrap.sh
```

## 5. Manual Assist Flow / 人工协助交互流程

### Case 1. Missing `USER_ID` / 缺少 `USER_ID`

The script pauses and asks:

```text
Enter the memory USER_ID:
```

You type a stable identifier such as:

```text
tars
```

脚本会暂停并提示：

```text
Enter the memory USER_ID:
```

你输入一个稳定标识，例如：

```text
tars
```

Then the script continues automatically.

输入后脚本会自动继续。

### Case 2. Missing timezone / 缺少时区

The script asks:

```text
Enter the system timezone [America/Los_Angeles]:
```

Press Enter to keep the default, or type another valid timezone.

脚本会提示：

```text
Enter the system timezone [America/Los_Angeles]:
```

直接回车表示保留默认值，也可以输入其他合法时区。

### Case 3. Non-interactive mode / 非交互模式

If you run the script in automation and do not provide required variables,
the script exits instead of guessing.

如果你在自动化环境里运行脚本，但没有提供必填变量，
脚本会直接退出，而不是擅自猜测。

Recommended pattern:

```bash
sudo USER_ID=tars TIMEZONE=America/Los_Angeles bash bootstrap/bootstrap.sh
```

推荐写法：

```bash
sudo USER_ID=tars TIMEZONE=America/Los_Angeles bash bootstrap/bootstrap.sh
```

## 6. Files Managed By This Repo / 本仓库接管的文件

The repo manages:

- `docker-compose.yml`
- `bootstrap/bootstrap.sh`
- `bootstrap/audit.sh`
- `workspace/skills/*`
- `workspace/.projects/true-recall/*`
- `workspace/HEARTBEAT.md`
- workspace docs/config files

本仓库接管的主要内容：

- `docker-compose.yml`
- `bootstrap/bootstrap.sh`
- `bootstrap/audit.sh`
- `workspace/skills/*`
- `workspace/.projects/true-recall/*`
- `workspace/HEARTBEAT.md`
- workspace 下的 docs/config 文件

## 7. What Bootstrap Writes On The Host / 脚本会在宿主机写入什么

Bootstrap writes or updates:

- `/home/openclaw/.memory_env`
- `/home/openclaw/.openclaw/workspace/.memory_env`
- `/home/openclaw/.openclaw/workspace/skills/...`
- `/home/openclaw/.openclaw/workspace/.projects/true-recall/...`
- user cron entries
- `/var/log/memory-capture.log`
- `/var/log/memory-backup.log`
- `/var/log/true-recall-curator.log`

bootstrap 会写入或更新：

- `/home/openclaw/.memory_env`
- `/home/openclaw/.openclaw/workspace/.memory_env`
- `/home/openclaw/.openclaw/workspace/skills/...`
- `/home/openclaw/.openclaw/workspace/.projects/true-recall/...`
- 用户级 cron
- `/var/log/memory-capture.log`
- `/var/log/memory-backup.log`
- `/var/log/true-recall-curator.log`

## 8. Default Schedule / 默认调度

Current default schedule:

- every 5 minutes: `cron_capture.py`
- `10:30`: `curate_memories.py`
- `11:00`: `cron_backup.py`
- `11:30`: `sliding_backup.sh`

当前默认调度为：

- 每 5 分钟：`cron_capture.py`
- `10:30`：`curate_memories.py`
- `11:00`：`cron_backup.py`
- `11:30`：`sliding_backup.sh`

These times assume the host timezone is `America/Los_Angeles`.

这些时间以宿主机时区 `America/Los_Angeles` 为基准。

## 9. How We Prevent OpenClaw Updates From Overwriting This Stack / 如何防止 OpenClaw 更新覆盖这套部署

This deployment is kept outside the OpenClaw application code.

这套部署没有把“源码真相”放进 OpenClaw 本体代码里。

That means:

- OpenClaw can update independently
- this repo remains the deployment source of truth
- rerunning bootstrap re-syncs managed files
- Docker services and cron are not tied to an OpenClaw package update

这意味着：

- OpenClaw 可以单独升级
- 本仓库仍然是部署的真实来源
- 重新执行 bootstrap 就能重新同步受管文件
- Docker 服务和 cron 不依赖 OpenClaw 包更新

Recommended recovery command after an OpenClaw update:

```bash
cd jarvismemory
sudo USER_ID=tars TIMEZONE=America/Los_Angeles bash bootstrap/bootstrap.sh
```

建议在 OpenClaw 更新后执行一次：

```bash
cd jarvismemory
sudo USER_ID=tars TIMEZONE=America/Los_Angeles bash bootstrap/bootstrap.sh
```

## 10. Post-Install Verification / 安装后验证

Run:

```bash
sudo bash bootstrap/audit.sh
```

or:

```bash
OPENCLAW_USER=openclaw OPENCLAW_HOME=/home/openclaw bash bootstrap/audit.sh
```

执行：

```bash
sudo bash bootstrap/audit.sh
```

或者：

```bash
OPENCLAW_USER=openclaw OPENCLAW_HOME=/home/openclaw bash bootstrap/audit.sh
```

Expected checks:

- Docker active
- Ollama active
- models present
- `kimi_memories` exists
- `true_recall` exists
- workspace files exist
- cron entries exist

预期检查项包括：

- Docker 正常
- Ollama 正常
- 模型存在
- `kimi_memories` 存在
- `true_recall` 存在
- workspace 文件存在
- cron 条目存在

## 11. Safe Re-run Behavior / 重复执行的安全性

You can rerun bootstrap after:

- OpenClaw reinstall
- OpenClaw update
- accidental workspace file drift
- missing cron entries

以下场景可以重复执行 bootstrap：

- OpenClaw 重装后
- OpenClaw 更新后
- workspace 文件漂移后
- cron 丢失后

Bootstrap is designed to **adopt and normalize** the deployment, not destroy it.

bootstrap 的设计目标是**接管并校正**部署，而不是破坏现有部署。

## 12. Recommended Future GitHub Workflow / 建议的后续 GitHub 流程

1. keep `main` as the stable branch
2. make future deployment changes in feature branches
3. review via PR before changing production
4. rerun bootstrap on the target VPS after merge

建议后续流程：

1. `main` 作为稳定分支
2. 未来修改在功能分支完成
3. 先走 PR，再改生产
4. 合并后在目标 VPS 上重新执行 bootstrap
