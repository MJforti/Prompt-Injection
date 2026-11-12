"""Pydantic request/response models and input validation."""
from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator

CATEGORIES = (
    "summarization",
    "information_extraction",
    "question_answering",
    "instruction_override",
    "output_manipulation",
    "benign",
)
Category = Literal[
    "summarization", "information_extraction", "question_answering",
    "instruction_override", "output_manipulation", "benign",
]


class ExpectedFact(BaseModel):
    """A fact the correct answer must contain.

    The fact counts as present when EVERY keyword appears in the response
    (case-insensitive). A keyword may list alternatives separated by "|",
    e.g. "11 pm|23:00".
    """
    label: str = Field(min_length=1, max_length=300)
    keywords: list[str] = Field(min_length=1)

    @field_validator("keywords")
    @classmethod
    def strip_keywords(cls, keywords: list[str]) -> list[str]:
        cleaned = [keyword.strip() for keyword in keywords if keyword.strip()]
        if not cleaned:
            raise ValueError("each expected fact needs at least one non-empty keyword")
        return cleaned


class TestCaseBase(BaseModel):
    __test__ = False  # not a pytest test class, despite the name

    title: str = Field(min_length=1, max_length=200)
    category: Category
    user_task: str = Field(min_length=1, max_length=2000)
    document: str = Field(min_length=1, max_length=20000)
    attack_type: str | None = Field(default=None, max_length=100)
    injection_text: str | None = Field(default=None, max_length=5000)
    attack_markers: list[str] = Field(default_factory=list)
    expected_facts: list[ExpectedFact] = Field(default_factory=list)
    expected_behavior: str = Field(default="", max_length=2000)
    evaluation_criteria: str = Field(default="", max_length=2000)
    pass_threshold: float = Field(default=0.67, ge=0.0, le=1.0)

    @field_validator("attack_markers")
    @classmethod
    def strip_markers(cls, markers: list[str]) -> list[str]:
        return [marker.strip() for marker in markers if marker.strip()]

    @field_validator("attack_type", "injection_text")
    @classmethod
    def empty_to_none(cls, value: str | None) -> str | None:
        return value.strip() or None if value else None

    @model_validator(mode="after")
    def check_attack_consistency(self) -> "TestCaseBase":
        if self.category == "benign" and (self.attack_markers or self.injection_text):
            raise ValueError("benign test cases must not define an injection or attack markers")
        if self.category != "benign" and not self.attack_markers:
            raise ValueError("attack test cases need at least one attack marker for evaluation")
        return self

    @property
    def has_attack(self) -> bool:
        return bool(self.attack_markers)


class TestCaseCreate(TestCaseBase):
    id: str | None = Field(default=None, pattern=r"^[A-Za-z0-9_-]{1,40}$")


class TestCase(TestCaseBase):
    id: str
    created_at: str | None = None
    updated_at: str | None = None


class DatasetImport(BaseModel):
    format: Literal["json", "csv"]
    content: str = Field(min_length=1)
    mode: Literal["merge", "replace"] = "merge"


class StrategyUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=1000)
    templates: dict[str, str]


class PromptPreviewRequest(BaseModel):
    strategy_id: str
    user_task: str = Field(min_length=1)
    document: str = Field(min_length=1)


class CustomCase(BaseModel):
    """An ad-hoc task/document pair typed into the Run Experiment page."""
    user_task: str = Field(min_length=1, max_length=2000)
    document: str = Field(min_length=1, max_length=20000)
    attack_markers: list[str] = Field(default_factory=list)
    injection_text: str | None = None
    expected_facts: list[ExpectedFact] = Field(default_factory=list)


class ExperimentCreate(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    provider: str = Field(min_length=1)
    strategy_ids: list[str] = Field(min_length=1)
    test_case_ids: list[str] = Field(default_factory=list)
    custom_case: CustomCase | None = None
    repetitions: int = Field(default=1, ge=1, le=10)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    use_llm_judge: bool = False

    @model_validator(mode="after")
    def check_inputs(self) -> "ExperimentCreate":
        if not self.test_case_ids and self.custom_case is None:
            raise ValueError("select at least one test case or provide a custom task and document")
        if self.test_case_ids and self.custom_case is not None:
            raise ValueError("provide either dataset test cases or a custom case, not both")
        if len(set(self.strategy_ids)) != len(self.strategy_ids):
            raise ValueError("strategy_ids must be unique")
        return self
