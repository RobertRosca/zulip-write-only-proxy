from __future__ import annotations

from tempfile import SpooledTemporaryFile
from typing import Annotated, Union

import fastapi
from fastapi.security import APIKeyHeader

from .. import __version__, __version_tuple__, models, services

_docs_url = "https://zulip.com/api/send-message#response"

router = fastapi.APIRouter(prefix="/api")

api_key_header = APIKeyHeader(name="X-API-key", auto_error=False)


def get_client(
    key: Annotated[str, fastapi.Security(api_key_header)]
) -> models.ScopedClient:
    if key is None:
        raise fastapi.HTTPException(status_code=403, detail="Not authenticated")

    try:
        return services.get_client(key)
    except KeyError as e:
        raise fastapi.HTTPException(
            status_code=401, detail="Unauthorised", headers={"HX-Location": "/"}
        ) from e


@router.post(
    "/send_message",
    response_description=f"See <a href='{_docs_url}'>{_docs_url}</a>",
)
def send_message(
    client: Annotated[models.ScopedClient, fastapi.Depends(get_client)],
    topic: Annotated[str, fastapi.Query(...)],
    content: Annotated[str, fastapi.Body(...)],
    image: Annotated[Union[fastapi.UploadFile, None], fastapi.File()] = None,
):
    if image:
        # Some screwing around to get the spooled tmp file to act more like a real file
        # since Zulip needs it to have a filename
        f: SpooledTemporaryFile = image.file  # type: ignore[assignment]
        f._file.name = image.filename  # type: ignore[misc, assignment]

        result = client.upload_file(f)

        content += f"\n[]({result['uri']})"

    return client.send_message(topic, content)


_docs_url = "https://zulip.com/api/update-message#response"


@router.patch(
    "/update_message",
    response_description=f"See <a href='{_docs_url}'>{_docs_url}</a>",
)
def update_message(
    client: Annotated[models.ScopedClient, fastapi.Depends(get_client)],
    message_id: Annotated[int, fastapi.Query(...)],
    propagate_mode: Annotated[models.PropagateMode, fastapi.Query(...)],
    content: Annotated[str | None, fastapi.Body(media_type="text/plain")] = None,
    topic: Annotated[str | None, fastapi.Query()] = None,
):
    if content or topic:
        return client.update_message(topic, content, message_id, propagate_mode)
    else:
        raise fastapi.HTTPException(
            status_code=400,
            detail=(
                "Either content (update message text) or topic (rename message topic) "
                "must be provided"
            ),
        )


_docs_url = "https://zulip.com/api/upload-file#response"


@router.post(
    "/upload_file",
    response_description=f"See <a href='{_docs_url}'>{_docs_url}</a>",
)
def upload_file(
    client: Annotated[models.ScopedClient, fastapi.Depends(get_client)],
    file: Annotated[fastapi.UploadFile, fastapi.File(...)],
):
    f: SpooledTemporaryFile = file.file  # type: ignore[assignment]
    f._file.name = file.filename  # type: ignore[misc, assignment]

    return client.upload_file(f)


_docs_url = "https://zulip.com/api/get-stream-topics#response"


@router.get(
    "/get_stream_topics",
    response_description=f"See <a href='{_docs_url}'>{_docs_url}</a>",
)
def get_stream_topics(
    client: Annotated[models.ScopedClient, fastapi.Depends(get_client)],
):
    return client.get_stream_topics()


@router.get("/me", response_model_exclude={"key"})
def get_me(
    client: Annotated[models.ScopedClient, fastapi.Depends(get_client)]
) -> models.ScopedClient:
    return client


@router.get("/health")
def healthcheck(request: fastapi.Request):
    return {
        "status": "OK",
        "dirty": "dirty" in __version__,
        "dev": "+" in __version__,
        "version": __version__,
        "version_tuple": __version_tuple__,
        "root_path": request.scope.get("root_path"),
    }