"""
Google Drive 上传模块 - 使用 API
"""
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

from pathlib import Path
import pickle

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# 配置
FOLDER_ID = "1LOGmTb5BUn2I4C_t-VC85W4F5C0bd3Hg"  # 你的 Google Drive 文件夹 ID
# OAuth helper files (create client_secrets.json via GCP console)
OAUTH_CLIENT_SECRETS = Path(__file__).parent / 'client_secrets.json'
OAUTH_TOKEN_FILE = Path.home() / '.gdrive_token.pickle'

def _get_service_account_path() -> Path:
    """Return a path to a service-account JSON if one is available."""
    possible_paths = [
        Path(__file__).parent / "credentials.json",
        Path.home() / ".keys" / "hale-monument-468122-s6-f6ead8a1c61b.json",
        Path.home() / "credentials.json",
    ]
    for path in possible_paths:
        if path.exists():
            return path
    return None


def _load_service_account_credentials():
    path = _get_service_account_path()
    if not path:
        return None
    return service_account.Credentials.from_service_account_file(
        str(path), scopes=SCOPES)


def _get_user_credentials():
    """Run the OAuth flow (or reuse a stored token) for a personal account."""
    creds = None
    # load existing token if available
    if OAUTH_TOKEN_FILE.exists():
        with OAUTH_TOKEN_FILE.open('rb') as f:
            creds = pickle.load(f)
    # refresh or perform flow as needed
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            if not OAUTH_CLIENT_SECRETS.exists():
                raise FileNotFoundError(
                    f"OAuth client secrets ({OAUTH_CLIENT_SECRETS}) not found. "
                    "Create a desktop OAuth client in the Google Cloud Console and "
                    "download the JSON here."
                )
            flow = InstalledAppFlow.from_client_secrets_file(
                str(OAUTH_CLIENT_SECRETS), SCOPES)
            creds = flow.run_local_server(port=0)
        # save the token for next run
        with OAUTH_TOKEN_FILE.open('wb') as f:
            pickle.dump(creds, f)
    return creds


def get_credentials():
    """Return Google credentials; prefer user OAuth if configured.

    If a `client_secrets.json` file is present *or* a saved user token exists we
    will run/refresh the OAuth flow.  Otherwise we fall back to a service
    account key (as before).
    """
    # if OAuth client info or token is available, use user credentials
    if OAUTH_CLIENT_SECRETS.exists() or OAUTH_TOKEN_FILE.exists():
        return _get_user_credentials()

    # otherwise try service account
    creds = _load_service_account_credentials()
    if creds:
        return creds

    raise FileNotFoundError(
        "No credentials available. Place a service-account JSON or provide "
        "`client_secrets.json` and perform OAuth flow."
    )

def upload_to_gdrive(file_path: str) -> str:
    """Upload a file into the configured Drive folder.

    Credentials are obtained via :func:`get_credentials`, which may return
    either a service-account or OAuth user token.  The returned object is
    passed directly to ``build`` so it works with both types.

    overwrite behavior: overwrite the file with same name if it already exists in the folder (Drive API will handle deduplication by content)
    """
    credentials = get_credentials()
    service = build('drive', 'v3', credentials=credentials)

    file_name = Path(file_path).name
    file_metadata = {
        'name': file_name,
        'parents': [FOLDER_ID]
    }

    media = MediaFileUpload(file_path, resumable=True)
    file = service.files().create(
        body=file_metadata,
        media_body=media,
        fields='id, webViewLink'
    ).execute()

    return file.get('webViewLink')

if __name__ == "__main__":
    # 测试
    test_file = Path(__file__).parent / "output" / "2026-03-02.mp3"
    if test_file.exists():
        try:
            creds = get_credentials()
            print(f"使用凭证类型: {type(creds)}")
            link = upload_to_gdrive(str(test_file))
            print(f"已上传: {link}")
        except Exception as e:
            print(f"错误: {e}")
