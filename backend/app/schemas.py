"""Public response contracts without fabricated prediction examples."""

from typing import Literal
from pydantic import BaseModel, Field


class ClassLabel(BaseModel):
    index: int
    code: str
    name: str


class ClassScore(ClassLabel):
    score: float = Field(ge=0, le=1, allow_inf_nan=False)


class ModelInfo(BaseModel):
    model_ready: bool
    unavailable_reason: str | None = None
    model_version: str | None = None
    architecture: str | None = None
    input_domain: str | None = None
    classes: list[ClassLabel] = Field(default_factory=list)
    score_type: Literal['uncalibrated_softmax'] | None = None
    calibrated: bool = False
    explanation_available: bool = False


class Health(BaseModel):
    status: Literal['ok'] = 'ok'
    model_ready: bool


class Explanation(BaseModel):
    available: Literal[False] = False
    reason: str = 'Grad-CAM is pending implementation and validation.'


class Quality(BaseModel):
    format: str
    width: int
    height: int
    technical_checks_passed: bool = True
    warnings: list[str] = Field(default_factory=lambda: [
        'Technical checks do not establish that the image is skin or within the training domain.'
    ])


class Prediction(BaseModel):
    request_id: str
    model_version: str
    input_domain: str
    predicted_class: ClassLabel
    scores: list[ClassScore]
    score_type: Literal['uncalibrated_softmax'] = 'uncalibrated_softmax'
    calibrated: Literal[False] = False
    explanation: Explanation = Field(default_factory=Explanation)
    quality: Quality
    limitations: list[str]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    request_id: str
    error: ErrorDetail
