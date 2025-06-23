環境準備 (最低要求)：
Python 3.8+
pip (Python 套件管理器)
專案啟動流程：
安裝依賴： 執行 pip install Django django-simple-captcha Pillow
資料庫遷移： 執行 python manage.py makemigrations board
            執行 python manage.py migrate
建立超級使用者： 執行 python manage.py createsuperuser (用於管理後台登入)
配置郵件服務： 在 my_messageboard/settings.py 中填寫您的 SMTP 郵箱資訊 (例如 Gmail 的應用程式專用密碼)。
運行開發伺服器： 執行 python manage.py runserver
主要存取路徑：
首頁 / 留言列表： http://127.0.0.1:8000/
發布留言： http://127.0.0.1:8000/post/ (需登入)
管理後台： http://127.0.0.1:8000/admin/
