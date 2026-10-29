from .config import ExecutionConfig
from .contracts import ExecutionRequest, RuntimeFamily


class RuntimePolicyError(ValueError):
    pass


class RuntimePolicy:
    def __init__(self, config: ExecutionConfig) -> None:
        self._images = config.runtime_images

    def select_image(self, request: ExecutionRequest) -> str:
        approved_image = self._images.get(request.runtime)
        if approved_image is None:
            raise RuntimePolicyError(
                f"no approved image is configured for runtime {request.runtime.value}"
            )
        if request.image is not None and request.image != approved_image:
            raise RuntimePolicyError("requested image is not approved for the runtime")
        return approved_image
