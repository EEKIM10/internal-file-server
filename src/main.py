import asyncio
import base64
import os
from datetime import datetime

import starlette.exceptions
from humanize import naturalsize
from functools import partial
from fastapi import FastAPI, HTTPException, Depends, Response, Request
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, PlainTextResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from pam import authenticate


base_html = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>Index of {directory}</title>{style}
</head>
<body><h1>Files in {directory}:</h1>
<table>{rows}</table>
</body>
</html>
"""

row_template = (
    "<tr><td><a href='{file_loc}' class='display-name'>{file_name}</a>{raw}</td>"
    "<td>last modified: {last_modified}</td><td class='file-size'>Size:"
    " <code>{file_size}</td></tr>"
)
style = (
    "<style>table tr { white-space: nowrap; }"
    "td.file-size { text-align: right; padding-left: 1em; } "
    "td.display-name { padding-left: 1em; padding-right: 1em; }</style>"
)


def escape(text: str):
    return text.replace("<", "&lt;").replace(">", "&gt;").replace("&", "&amp;")


class FallbackStaticFiles(StaticFiles):
    async def get_response(self, path: str, scope) -> Response:
        authorise(await basic(Request(scope)))
        try:
            return await super().get_response(path, scope)
        except starlette.exceptions.HTTPException:
            rows = []
            _path = Path(path).resolve().relative_to(Path.cwd())
            if _path.is_dir():
                for _p in _path.iterdir():
                    stat = _p.stat()
                    size = naturalsize(stat.st_size, False, True)
                    last_modified = datetime.fromtimestamp(stat.st_mtime).strftime("%c")
                    raw = ""
                    if not _p.is_dir():
                        raw = " (<a href='/_special/view_plain?path={}'>View Raw</a>)".format("./" + str(_p))
                    rows.append(
                        row_template.format(
                            file_loc=escape("./" + str(_p)),
                            file_name=escape(_p.name),
                            file_size=size,
                            last_modified=last_modified,
                            raw=raw,
                        )
                    )
            else:
                if not _path.exists():
                    raise HTTPException(404, "File '%s' does not exist." % _path)
                return FileResponse(_path)
            new = base_html.format(directory=str(_path), rows="\n".join(rows), style=style)
            return HTMLResponse(new)


basic = HTTPBasic(realm="PAM", description="PAM Login")


def authorise(credentials: HTTPBasicCredentials = Depends(basic)):
    print(
        "Authorising username %r with password %r"
        % (credentials.username, credentials.password[:2] + ("*" * (len(credentials.password) - 2)))
    )
    okay = False
    try:
        okay = authenticate(
            credentials.username,
            credentials.password,
        )
    except TypeError:
        username = os.getenv("HTTP_FILE_SERVER_USERNAME")
        password = os.getenv("HTTP_FILE_SERVER_PASSWORD")
        if username and password:
            if username == credentials.username:
                if password == credentials.password:
                    # I'm too lazy to care about timing attacks here
                    okay = True
        else:
            raise HTTPException(501, "Password Authentication Unvailable.")
    if not okay:
        raise HTTPException(401, headers={"WWW-Authenticate": "Basic realm=PAM"})
    return True


app = FastAPI(dependencies=[Depends(authorise)])


@app.get("/_special/view_plain")
async def read_plain(path: str):
    path = Path(path).resolve()
    if not path.exists():
        raise HTTPException(404, "file not found")
    if path.is_dir():
        raise HTTPException(400, "cannot read directory")
    if not path.is_relative_to(Path.cwd()):
        raise HTTPException(403, "directory is outside runtime scope")

    try:
        return FileResponse(path, media_type="text/plain")
    except PermissionError:
        raise HTTPException(403, "failed to read file")
    except asyncio.TimeoutError:
        raise HTTPException(504, "file took too long to read")


app.mount("/", FallbackStaticFiles(directory=Path.cwd()))

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, port=8080)
