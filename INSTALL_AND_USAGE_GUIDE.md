# 安裝 SOP 與使用說明 - 我的留言板項目

## 1. 概述

本文件旨在提供在 Windows、Linux 和 macOS 作業系統上安裝和運行“我的留言板”項目的標準作業流程 (SOP) 和基本使用說明。項目基於 Python 和 Django 框架開發。

## 2. 環境要求

在開始之前，請確保您的系統已安裝以下軟體：

*   **Python**: 版本 3.8 或更高版本。
    *   **驗證**: 在終端或命令提示字元中輸入 `python --version` 或 `python3 --version`。
*   **pip (Python 套件管理器)**: 通常隨 Python 一同安裝。
    *   **驗證**: 輸入 `pip --version` 或 `pip3 --version`。
*   **Git**: 用於從版本控制系統下載項目（如果適用）。
    *   **驗證**: 輸入 `git --version`。

## 3. 安裝步驟

以下步驟適用於所有主要作業系統 (Windows, Linux, macOS)，但部分命令可能因作業系統而略有不同。

### 3.1. 下載項目代碼

*   **選項 A: 使用 Git 克隆 (推薦)**
    ```bash
    git clone <repository_url> # 將 <repository_url> 替換為實際的 Git 倉庫 URL
    cd <project_directory_name> # 進入項目目錄
    ```
*   **選項 B: 下載 ZIP 文件**
    如果您從某處下載了項目的 ZIP 壓縮包，請將其解壓縮到您選擇的文件夾中，並通過終端進入該文件夾。

### 3.2. 創建並激活虛擬環境 (強烈推薦)

為避免套件版本衝突，建議在項目特定的虛擬環境中安裝依賴。

*   **創建虛擬環境**:
    ```bash
    python -m venv venv  # 或者 python3 -m venv venv
    ```
    這會在項目目錄下創建一個名為 `venv` 的虛擬環境文件夾。

*   **激活虛擬環境**:
    *   **Windows (cmd.exe)**:
        ```bash
        venv\Scripts\activate.bat
        ```
    *   **Windows (PowerShell)**:
        ```bash
        venv\Scripts\Activate.ps1
        ```
        (如果遇到執行策略問題，您可能需要先運行 `Set-ExecutionPolicy Unrestricted -Scope Process` 或 `Set-ExecutionPolicy RemoteSigned -Scope Process`)
    *   **Linux / macOS (bash/zsh)**:
        ```bash
        source venv/bin/activate
        ```
    激活成功後，您的命令提示字元前通常會顯示 `(venv)`。

### 3.3. 安裝項目依賴

項目依賴項已在 `requirements.txt` 文件中列出。

如果您有 `requirements.txt` 文件 (項目根目錄應包含此文件)，請使用以下命令安裝所有依賴：
```bash
pip install -r requirements.txt
```
這將安裝 Django、django-simple-captcha、Pillow 以及部署到 Render 所需的額外包（如 gunicorn, dj_database_url, psycopg2-binary, whitenoise）。

### 3.4. 配置郵件服務 (可選，用於郵件通知功能)

如果您希望留言審核通知、密碼重設等郵件功能正常工作，需要配置 SMTP 郵件服務。

1.  打開 `my_messageboard/settings.py` 文件。
2.  找到以下郵件配置部分：
    ```python
    # EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    # EMAIL_HOST = 'smtp.gmail.com'
    # EMAIL_PORT = 587
    # EMAIL_USE_TLS = True
    # EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    # EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    # DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', 'webmaster@localhost')
    # ADMINS = [('Admin', os.environ.get('ADMIN_EMAIL'))] if os.environ.get('ADMIN_EMAIL') else []
    ```
3.  **重要**: 為了實際發送郵件，您需要：
    *   將 `EMAIL_BACKEND` 改為 `'django.core.mail.backends.smtp.EmailBackend'`。
    *   填寫您的 SMTP 服務器信息 (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`)。
    *   **安全建議**: 強烈建議將 `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`, 和管理員郵箱 (`ADMIN_EMAIL`) 存儲為**環境變量**，而不是直接硬編碼到 `settings.py` 文件中。
        *   例如，在 Linux/macOS 的 `.bashrc` 或 `.zshrc` 中設置：
            ```bash
            export EMAIL_HOST_USER="your_email@example.com"
            export EMAIL_HOST_PASSWORD="your_app_password"
            export DEFAULT_FROM_EMAIL="your_email@example.com"
            export ADMIN_EMAIL="admin_email@example.com"
            ```
        *   在 Windows 中，可以通過系統屬性設置環境變量。
    *   如果使用 Gmail，您可能需要為您的帳戶生成一個“應用程式專用密碼”，並在 `EMAIL_HOST_PASSWORD` 中使用它，而不是您的常規 Gmail 密碼。同時確保您的 Gmail 帳戶允許安全性較低的應用程式訪問（如果未使用應用程式專用密碼）。
4.  如果暫時不需要真實郵件功能，可以保持 `EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'`，這樣郵件內容會打印到運行服務器的控制台。

### 3.5. 數據庫遷移

Django 使用遷移來管理數據庫結構。

1.  **生成遷移文件** (通常在模型更改後執行，但首次設置時運行無害):
    ```bash
    python manage.py makemigrations board
    python manage.py makemigrations captcha # 如果 captcha 應用有自己的遷移
    ```
2.  **應用遷移到數據庫**:
    ```bash
    python manage.py migrate
    ```
    這將創建項目所需的數據庫表。根據 `my_messageboard/settings.py` 中的配置，SQLite 數據庫文件名默認為 `db_init_v1.sqlite3`。
    *   **首次設置**：如果 `db_init_v1.sqlite3` 文件不存在，Django 會自動創建它。
    *   **從舊版本遷移 (如果原使用 `db.sqlite3`)**：如果您是從一個使用 `db.sqlite3` 作為數據庫文件的舊版本項目更新而來，請確保在運行 `migrate` 命令**之前**，已將您現有的 `db.sqlite3` 文件手動重命名為 `db_init_v1.sqlite3`，以保留數據。否則，將創建一個新的空數據庫。

### 3.6. 創建超級使用者 (管理員帳戶)

管理員帳戶用於訪問後台管理界面。

```bash
python manage.py createsuperuser
```
按照提示輸入用戶名、電子郵件（可選）和密碼。

## 4. 運行開發服務器

```bash
python manage.py runserver
```
服務器默認會在 `http://127.0.0.1:8000/` 上運行。您可以在瀏覽器中打開此地址。

*   **指定不同端口**: `python manage.py runserver 8080`
*   **允許其他設備訪問 (慎用，注意防火牆)**: `python manage.py runserver 0.0.0.0:8000`

## 5. 使用說明

### 5.1. 主要訪問路徑

*   **首頁 / 留言列表**: `http://127.0.0.1:8000/`
    *   顯示所有已審核的留言。
    *   提供分頁功能。
*   **註冊新帳戶**: 點擊導航欄上的 "註冊" 按鈕，或訪問 `http://127.0.0.1:8000/accounts/signup/`
    *   填寫用戶名、電子郵件和密碼進行註冊。
*   **登入**: 點擊導航欄上的 "登入" 按鈕，或訪問 `http://127.0.0.1:8000/accounts/login/`
*   **登出**: 登入後，點擊導航欄上的 "登出" 按鈕。
*   **發布留言**: `http://127.0.0.1:8000/post/` (需要登入)
    *   填寫主題、內容和驗證碼來提交新留言。留言提交後需要等待管理員審核。
*   **密碼重設**:
    *   請求密碼重設: `http://127.0.0.1:8000/accounts/password_reset/`
    *   (後續步驟將通過郵件指引，如果郵件服務已配置)
*   **管理後台**: `http://127.0.0.1:8000/admin/`
    *   使用第 3.6 步創建的超級使用者帳戶登入。
    *   管理員可以在此審核留言、管理用戶等。
        *   **審核留言**: 進入 "Board" -> "留言" 部分。
            *   可以單獨審核，或批量選擇留言進行 "批量通過選中留言並郵件通知" 或 "批量取消通過選中的留言"。
            *   可以直接在留言編輯頁面勾選/取消 "是否通過審核" 並保存。
            *   有 "快速通過所有未審核留言並通知" 的快捷按鈕。
        *   審核通過且用戶提供了郵箱時，系統會嘗試發送郵件通知。
        *   新留言提交後，管理員（需在 `settings.py` 中配置 `ADMINS` 郵箱並啟用真實郵件後端）會收到郵件通知。

### 5.2. 停止開發服務器

在運行服務器的終端中，按 `Ctrl+C`。

### 5.3. 退出虛擬環境

完成工作後，可以退出虛擬環境：
```bash
deactivate
```

## 6. 平台差異性注意事項

*   **文件路徑**: Windows 使用反斜杠 `\` 作為路徑分隔符，而 Linux 和 macOS 使用正斜杠 `/`。Python 通常能很好地處理這種差異，但在手動編寫路徑時需注意。
*   **環境變量設置**: 如 3.4 節所述，設置環境變量的方法因作業系統而異。
*   **Pillow (圖像處理庫) 的依賴**: Pillow 可能有一些底層的圖像庫依賴 (如 libjpeg, zlib)。
    *   **Linux**: 通常可以使用系統的包管理器安裝，例如：
        ```bash
        sudo apt-get install libjpeg-dev zlib1g-dev (Debian/Ubuntu)
        sudo yum install libjpeg-turbo-devel zlib-devel (Fedora/CentOS)
        ```
    *   **macOS**: 使用 Homebrew 可以安裝：
        ```bash
        brew install jpeg zlib
        ```
    *   **Windows**: Pillow 的 Wheel 包通常包含了預編譯的二進制文件，一般不需要額外步驟。
    如果在 `pip install Pillow` 時遇到編譯錯誤，通常是缺少這些依賴。
*   **命令行工具**: `python` vs `python3`, `pip` vs `pip3`。在某些系統中，您可能需要使用帶有 `3` 的版本（例如 `python3 manage.py runserver`）。建議在虛擬環境中統一使用 `python` 和 `pip`。
*   **防火牆**: 如果您使用 `0.0.0.0` 使服務器可被網絡中其他設備訪問，請確保操作系統的防火牆允許相應端口的傳入連接。

## 7. 故障排除

*   **`ModuleNotFoundError: No module named 'django'` (或類似錯誤)**:
    *   確保您已激活虛擬環境。
    *   確保已成功執行 `pip install -r requirements.txt` (如果使用該文件) 或單獨安裝了所有依賴。
*   **數據庫錯誤 (例如 `no such table`)**:
    *   確保已運行 `python manage.py migrate`。
*   **驗證碼不顯示或出錯**:
    *   確保 `Pillow` 已正確安裝並且其依賴也已滿足。
    *   檢查 `settings.py` 中的 `CAPTCHA_*` 配置是否正確。
    *   確保 `captcha` 應用已添加到 `INSTALLED_APPS` 並且 `path('captcha/', include('captcha.urls'))` 已添加到 `my_messageboard/urls.py`。
*   **郵件發送失敗**:
    *   檢查 `my_messageboard/settings.py` 中的郵件配置是否正確。
    *   確保 `EMAIL_HOST_USER` 和 `EMAIL_HOST_PASSWORD` (或應用程式專用密碼) 正確無誤。
    *   檢查您的郵件服務提供商是否有任何安全限制 (例如，Gmail 的“安全性較低的應用程式訪問權限”或兩步驗證設置)。
    *   檢查網絡連接和防火牆設置，確保可以訪問 SMTP 服務器和端口。

本指南提供了基本的安裝和使用流程。根據您的具體環境，可能需要進行額外的調整。

## 8. 部署到 Render.com (示例)

以下是將此項目部署到 Render.com 的一些關鍵步驟和注意事項。

### 8.1. 準備工作 (已在前面步驟中部分完成)

*   **`requirements.txt`**: 確保已包含 `gunicorn`, `dj_database_url`, `psycopg2-binary`, `whitenoise`。
*   **`Procfile`**: 項目根目錄下應有 `Procfile`，內容類似：
    ```
    web: gunicorn my_messageboard.wsgi --log-file - --log-level info
    release: python manage.py migrate
    ```
*   **`runtime.txt` (可選)**: 如果您希望指定 Python 版本，例如：
    ```
    python-3.11.4
    ```
*   **`settings.py`**: 已針對生產環境進行了調整，以從環境變量讀取敏感配置，並配置了數據庫 (優先使用 `DATABASE_URL`) 和靜態文件 (WhiteNoise)。

### 8.2. Render 服務配置

1.  **創建 Render 帳戶並登入**。
2.  **新建 Web Service**：
    *   選擇從您的 Git 倉庫 (例如 GitHub) 部署。
    *   連接到包含此項目的倉庫。
3.  **配置服務**：
    *   **名稱**: 給您的服務起一個名字。
    *   **Region**: 選擇服務器區域。
    *   **Branch**: 選擇要部署的分支 (例如 `main` 或 `master`)。
    *   **Root Directory**: 通常留空 (如果 `requirements.txt`, `Procfile` 等在倉庫根目錄)。
    *   **Runtime**: Render 通常能自動檢測到 Python。如果創建了 `runtime.txt`，它會使用指定的版本。
    *   **Build Command**: Render 通常會自動填充為類似 `pip install -r requirements.txt && python manage.py collectstatic --noinput --clear`。您可以根據需要調整，但 `python manage.py migrate` 已由 `Procfile` 中的 `release` 階段處理。
    *   **Start Command**: Render 會自動從 `Procfile` 讀取 `web` 進程的命令，即 `gunicorn my_messageboard.wsgi --log-file - --log-level info`。
4.  **添加數據庫 (推薦)**：
    *   在 Render 上創建一個 PostgreSQL 數據庫實例。
    *   創建後，Render 會提供一個 `DATABASE_URL` (內部連接字符串)。
    *   將此 `DATABASE_URL` 添加到您的 Web Service 的環境變量中。`settings.py` 中的 `dj_database_url.config()` 會自動使用它。
    *   **重要**: SQLite 不適用於 Render 的生產環境，因為其文件系統是臨時的，數據會在重啟或重新部署時丟失。**務必使用 Render 提供的 PostgreSQL 或類似的持久化數據庫服務。**
5.  **設置環境變量**:
    *   在 Render 服務的 "Environment" 選項卡中，添加所有必要的環境變量，例如：
        *   `DJANGO_SECRET_KEY`: 一個長而隨機的字符串 (不要使用開發時的默認值)。
        *   `DJANGO_DEBUG`: 設置為 `False`。
        *   `DJANGO_ALLOWED_HOSTS`: 您的 Render 應用域名 (例如 `your-app-name.onrender.com`) 以及任何自定義域名，用逗號分隔。
        *   `DATABASE_URL`: (如果使用 Render 的數據庫，它可能會自動注入，或者您需要從數據庫服務的設置中複製過來)。
        *   `DJANGO_CSRF_TRUSTED_ORIGINS`: 您的應用程序將通過 HTTPS 訪問的域名，例如 `https://your-app-name.onrender.com`。
        *   `DJANGO_SECURE_SSL_REDIRECT`: 設置為 `True` (如果 Render 配置了自動 HTTPS)。
        *   `DJANGO_SESSION_COOKIE_SECURE`: 設置為 `True`。
        *   `DJANGO_CSRF_COOKIE_SECURE`: 設置為 `True`。
        *   郵件相關環境變量 ( `DJANGO_EMAIL_HOST_USER`, `DJANGO_EMAIL_HOST_PASSWORD`, `DJANGO_DEFAULT_FROM_EMAIL` 等)，如果您希望郵件功能在生產中工作。
        *   `DJANGO_ADMIN_EMAIL`: 用於管理員通知和“聯絡管理員”功能。
6.  **部署**: 保存配置後，Render 將開始構建和部署您的應用。您可以在 "Events" 或 "Logs" 中查看部署進度。

### 8.3. 部署後檢查

*   訪問您的 Render 應用 URL，檢查網站是否正常運行。
*   測試用戶註冊、登入、發布留言、管理後台等功能。
*   檢查日誌中是否有錯誤。

以上是部署到 Render 的大致流程和關鍵配置。具體細節可能會因 Render 平台的更新而略有變化，建議同時參考 Render 的官方文檔。
```
