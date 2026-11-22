# Expense ReAct Agent
### 個人記帳與預算超支診斷智慧代理系統

以自然語言完成記帳、消費查詢與預算診斷的本地 AI 財務助理。

---

## 專案簡介

**Expense ReAct Agent** 是一套以 **ReAct（Reasoning + Acting）** 架構設計的命令列（CLI）個人財務智慧代理系統。使用者可以透過自然語言輸入消費內容，系統會由大型語言模型（LLM）理解需求，再透過 Function Calling 呼叫對應的財務工具，完成資料新增、查詢與預算分析。

本專案預設串接本機 **Ollama**，使用 `qwen2.5:7b` 模型，並以 **SQLite** 儲存消費紀錄及預算設定。除了單筆記帳，也支援從同一句話中辨識多筆消費、自動分類，以及檢查各類別的預算使用情形與超支風險。

### 核心功能

- **自然語言記帳**：直接輸入日常消費描述，不必手動填寫表單。
- **多筆消費拆分**：從一句話中辨識多筆不同金額或類別的消費。
- **消費紀錄查詢**：依日期區間及消費類別查詢歷史紀錄與金額總和。
- **預算管理**：新增或更新各消費類別的每月預算上限。
- **預算風險診斷**：計算預算使用率、剩餘預算、每日可用額度及高額消費。
- **本地模型與資料儲存**：透過 Ollama 執行模型，並使用 SQLite 保存資料。

---

## 專案目標

本專案將大型語言模型的自然語言理解能力，結合 ReAct Agent 的工具使用機制與 SQLite 資料管理，打造一個能夠理解使用者記帳需求、執行實際資料操作，並提供預算風險提示的個人財務助理。

相較於傳統需要手動選擇分類、輸入金額及逐筆儲存的記帳方式，使用者只需透過自然語言描述消費，即可完成記帳與預算檢視，讓日常財務管理更加直覺且有效率。

---

## 系統架構與運作流程

系統以 ReAct 流程串接語言模型與財務工具，讓模型依照使用者需求決定要呼叫哪些工具，再根據工具回傳結果組織回答。

```text
使用者自然語言輸入
        │
        ▼
   CLI 互動介面
     (main.py)
        │
        ▼
 ReAct Agent 核心
    (agent.py)
        │
        ├── Thought：分析使用者需求
        │
        ├── Action：選擇並呼叫財務工具
        │       │
        │       ▼
        │    tools.py
        │       │
        │       ▼
        │    database.py
        │       │
        │       ▼
        │    SQLite 資料庫
        │
        └── Observation：讀取工具執行結果
                │
                ▼
          整理並回覆使用者
```

### ReAct 執行階段

1. **Thought（思考）**：分析使用者輸入，判斷需要記帳、查詢、調整預算或執行預算診斷。
2. **Action（行動）**：透過 Function Calling 選擇適合的工具，並傳入所需參數。
3. **Observation（觀察）**：取得工具執行結果，例如新增紀錄、查詢金額或預算使用率。
4. **迭代與回覆**：若任務尚未完成，Agent 可繼續呼叫工具；完成後再依據工具結果產生自然語言回覆。

> **數據處理原則：** 涉及消費金額、統計結果及預算使用率時，應以資料庫或工具實際回傳的結果為準，不應由語言模型自行推算後當成資料庫結果。

---

## 專案目錄與檔案說明

```text
expense-react-agent/
│
├── src/
│   ├── __init__.py       # Python 套件初始化宣告
│   ├── main.py           # CLI 互動式主程式進入點
│   ├── agent.py          # ReAct Agent 核心與推理迴圈
│   ├── tools.py          # 財務工具函式、JSON Schema 與工具分派
│   ├── database.py       # SQLite 連線與資料表初始化
│   └── demo.py           # 自動化展示與測試腳本
│
├── data/
│   └── finance.db        # SQLite 資料庫（執行時自動建立）
│
├── .env                  # 環境變數設定（需自行建立）
├── requirements.txt      # Python 相依套件清單
├── Dockerfile            # Docker／Podman 映像檔建置設定
└── README.md             # 專案說明文件
```

### 核心程式模組

| 檔案 | 功能與職責 |
|---|---|
| `src/main.py` | 提供終端機互動介面（REPL）；載入 `.env`、設定 UTF-8 輸入輸出、初始化資料庫並啟動 Agent。支援 `exit`／`quit` 離開，也會處理缺少互動終端機時可能發生的 `EOFError`。 |
| `src/agent.py` | 封裝 `ExpenseReActAgent`，負責 LLM 呼叫、Thought／Action／Observation 流程及推理迴圈控制。透過 OpenAI 相容 API 連接 Ollama，並注入系統提示詞。 |
| `src/tools.py` | 定義 Agent 可使用的財務工具、`TOOLS_SCHEMA` 與 `TOOL_DISPATCHER`，負責參數驗證及工具分派。 |
| `src/database.py` | 管理 SQLite 連線與資料表初始化。預設讀取 `DB_PATH`；若未設定，資料庫路徑為 `/app/data/finance.db`。初始化時建立 `expenses` 與 `budgets` 資料表，並寫入六大分類的預設月預算。 |
| `src/demo.py` | 執行預設展示情境，示範設定預算、連續記錄多筆消費及預算診斷，方便觀察多工具呼叫與 Agent 執行流程。 |
| `src/__init__.py` | 將 `src` 標示為 Python 套件目錄。 |

### 財務工具一覽

`src/tools.py` 提供以下四個核心工具：

| 工具名稱 | 用途 |
|---|---|
| `record_expense` | 驗證消費日期與金額，將單筆消費寫入 `expenses` 資料表。 |
| `query_expenses` | 依日期區間及指定類別查詢消費明細與金額總和。 |
| `diagnose_budget_status` | 計算指定月份、指定類別的預算使用率、預警狀態、剩餘日均可用額度，以及該類別前三高額消費。 |
| `set_category_budget` | 新增或更新指定消費類別的每月預算上限。 |

### 環境與部署檔案

- **`.env`**：集中管理 LLM API 位址、API Key、模型名稱及資料庫路徑，避免將環境設定直接寫在程式碼中。
- **`requirements.txt`**：列出專案執行所需的 Python 套件。
- **`Dockerfile`**：以 `python:3.11-slim` 為基礎映像，安裝相依套件、複製程式碼、建立 `/app/data` 目錄，並以 `python src/main.py` 作為預設啟動指令。

---

## 預算分類與診斷規則

### 六大消費分類

系統初始化時會建立以下六種消費分類及預設每月預算，目前這個功能只是方便進行測試而已：

| 消費類別 | 預設月預算 |
|---|---:|
| 餐飲 | NT$6,000 |
| 交通 | NT$2,000 |
| 娛樂 | NT$3,000 |
| 學習 | NT$2,000 |
| 生活 | NT$3,000 |
| 其他 | NT$2,000 |
| **合計** | **NT$18,000** |

### 三級預算預警機制

系統依照「預算使用率」判斷目前的預算狀態：

| 狀態 | 判斷條件 | 系統意義 |
|---|---:|---|
| `GREEN_OK` | 使用率 < 80% | 預算使用正常。 |
| `WARNING_80%` | 80% ≤ 使用率 < 100% | 進入預算警戒區，提醒使用者留意後續支出，並提供前三高額消費與每日可用額度等資訊。 |
| `RED_ALERT` | 使用率 ≥ 100% | 已達到或超過預算上限，觸發超支警示。 |

**計算方式**

- 預算使用率 = 當月該類別累計支出 ÷ 該類別月預算 × 100%
- 剩餘預算 = 該類別月預算 − 當月該類別累計支出
- 每日可用額度（`daily_allowance`）及前三高額消費（`top3_expenses`）由 `diagnose_budget_status` 工具計算並回傳。

> 若剩餘預算為負數，代表該類別已超支。每日可用額度的實際計算方式，仍以程式中 `diagnose_budget_status` 的實作為準。

---

## 環境需求與準備

開始執行前，請先確認已準備以下環境：

- Python 3.11
- Ollama
- `qwen2.5:7b` 模型
- Docker 或 Podman（若要使用容器執行）

### 1. 下載模型

先確認 Ollama 已安裝，再下載本專案預設使用的模型：

```bash
ollama pull qwen2.5:7b
```

### 2. 啟動 Ollama

```bash
ollama serve
```

若 Ollama 已經以背景服務方式啟動，通常不需要再開啟第二個服務程序。

**容器連線注意事項：** 若 Agent 在 Docker／Podman 容器內執行，而 Ollama 在主機上執行，Ollama 必須允許容器連線。請依作業系統及 Ollama 安裝方式設定服務監聽位址（例如 `OLLAMA_HOST=0.0.0.0:11434`），並確認防火牆及容器網路設定允許連線。不要將容器內的 `localhost` 誤當成主機的 `localhost`。

---

## 安裝與執行方式

本專案提供兩種執行方式，可依照使用情境選擇。

## 方法一：使用 Docker／Podman（推薦）

容器方式可以統一 Python 執行環境，並透過 Volume 將 SQLite 資料庫保存在主機上。

### 步驟 1：確認相依套件

確認專案根目錄中的 `requirements.txt` 至少包含：

```text
openai>=1.0.0
python-dotenv>=1.0.0
```

### 步驟 2：建立環境變數檔

在專案根目錄建立 `.env`。以下為容器連線設定範例；請依實際環境調整 Ollama 位址：

```env
LLM_BASE_URL=http://host.containers.internal:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b
DB_PATH=/app/data/finance.db
```

- Podman 通常可使用 `host.containers.internal` 連接主機。
- Docker Desktop 通常可使用 `host.docker.internal`。
- 若 Docker 環境無法解析 `host.docker.internal`，可視環境需求搭配 `--add-host=host.docker.internal:host-gateway`。

### 步驟 3：建置容器映像檔

在專案根目錄執行：

```bash
# Podman
podman build -t expense-agent .

# Docker
docker build -t expense-agent .
```

### 步驟 4：啟動互動式記帳系統

```bash
# Podman
podman run --rm -it \
  --env-file .env \
  -v ./data:/app/data \
  expense-agent

# Docker
docker run --rm -it \
  --env-file .env \
  -v ./data:/app/data \
  expense-agent
```

**參數說明**

- `--rm`：容器結束後自動移除容器。
- `-it`：開啟互動式終端機，讓使用者能輸入記帳指令。
- `--env-file .env`：載入環境變數。
- `-v ./data:/app/data`：將主機的 `data/` 目錄掛載到容器，讓資料庫檔案在容器刪除後仍可保留。

> 請先確認主機上的 `data/` 目錄存在；若尚未建立，可先執行 `mkdir -p data`。Windows PowerShell 可使用 `New-Item -ItemType Directory -Force data`。

### 步驟 5：執行自動化 Demo

若想直接觀看預設測試情境及多工具連續呼叫結果，可覆寫容器的預設啟動指令：

```bash
# Podman
podman run --rm -it \
  --env-file .env \
  -v ./data:/app/data \
  expense-agent python src/demo.py

# Docker
docker run --rm -it \
  --env-file .env \
  -v ./data:/app/data \
  expense-agent python src/demo.py
```

---

## 方法二：使用本機 Python 環境

若不使用容器，也可以直接在 Windows、macOS 或 Linux 執行。此方式請將 `.env` 中的 Ollama 位址設定為本機位址，並使用本機可寫入的資料庫路徑。

### 步驟 1：建立並啟動虛擬環境

```bash
# 建立虛擬環境
python -m venv .venv

# Windows（PowerShell）
.venv\Scripts\Activate.ps1

# Windows（CMD）
.venv\Scripts\activate.bat

# macOS / Linux
source .venv/bin/activate
```

### 步驟 2：安裝相依套件

```bash
pip install -r requirements.txt
```

若尚未建立 `requirements.txt`，也可以先執行：

```bash
pip install openai python-dotenv
```

### 步驟 3：設定本機版 `.env`

在專案根目錄建立或修改 `.env`：

```env
LLM_BASE_URL=http://localhost:11434/v1
LLM_API_KEY=ollama
LLM_MODEL=qwen2.5:7b
DB_PATH=./data/finance.db
```

### 步驟 4：啟動程式

```bash
# 啟動互動式記帳模式
python src/main.py

# 或執行範例 Demo
python src/demo.py
```

---

## 常見問題與排解方式

### 1. 啟動容器時出現 `EOFError` 或無法讀取標準輸入

**可能原因：** 執行 `podman run` 或 `docker run` 時沒有加上互動終端機參數。

**解決方式：** 在執行指令中加入 `-it`：

```bash
podman run --rm -it --env-file .env -v ./data:/app/data expense-agent
```

### 2. Agent 無法連線 Ollama（`Connection refused`）

**可能原因：** Ollama 尚未啟動、連線位址設定錯誤，或容器無法連接主機服務。

**解決方式：**

- 確認 Ollama 服務正在執行。
- 確認模型已下載：`ollama list`。
- 本機執行時，確認 `.env` 使用 `http://localhost:11434/v1`。
- 容器執行時，確認 `.env` 使用可從容器連到主機的位址，例如 Podman 的 `host.containers.internal`。
- 確認 Ollama 服務監聽設定、防火牆與容器網路允許連線。

### 3. 本機執行時出現 `PermissionError: [Errno 13] Permission denied: '/app'`

**可能原因：** 未設定 `DB_PATH`，程式便使用預設容器路徑 `/app/data/finance.db`；一般本機使用者可能沒有 `/app` 的寫入權限。

**解決方式：** 在 `.env` 明確設定本機路徑：

```env
DB_PATH=./data/finance.db
```

並確認 `data/` 目錄存在且具有寫入權限。

### 4. 容器執行後資料沒有保留

**可能原因：** 啟動容器時沒有掛載資料目錄，資料庫只寫入容器內部。

**解決方式：** 使用 Volume 掛載：

```bash
-v ./data:/app/data
```

並確認程式中的 `DB_PATH` 與容器內掛載路徑一致。

---

## 專案設定與安全提醒

- **保護 `.env`**：若 `.env` 含有 API Key 或其他連線資訊，請勿將其提交至公開 GitHub 儲存庫。
- **排除資料庫與虛擬環境**：建議在 `.gitignore` 中排除 `.env`、`.venv/`、`__pycache__/`、`data/*.db` 等本機檔案。
- **備份資料庫**：消費紀錄儲存在 SQLite 檔案中，建議定期備份 `data/finance.db`。
- **確認模型與服務可用**：執行 Agent 前，請先確認 Ollama 已啟動且指定模型可正常使用。
- **注意資料正確性**：自然語言辨識可能受描述方式影響；記帳後可再使用查詢功能確認日期、類別及金額。

---

## 技術組成

| 類別 | 使用技術 | 用途 |
|---|---|---|
| 程式語言 | Python 3.11 | 系統主要開發語言 |
| Agent 架構 | ReAct | 串接推理、工具呼叫與結果觀察 |
| 語言模型服務 | Ollama | 在本機執行大型語言模型 |
| 預設模型 | `qwen2.5:7b` | 理解自然語言及決定工具呼叫 |
| 工具介面 | OpenAI 相容 API／Function Calling | 讓模型選擇並呼叫財務工具 |
| 資料庫 | SQLite | 儲存消費紀錄與預算設定 |
| 環境管理 | `python-dotenv` | 載入 `.env` 環境變數 |

---

## 尚未完成內容

- 本專案目前還只能利用 Powershell 運行，方便操作的介面部分尚未想好所需的內容
- 預設預算部分只是方便先進行測試時設定，未來在正式完成 Project 時會拿掉