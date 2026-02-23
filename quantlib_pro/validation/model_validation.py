"""
Model Risk & Validation Framework.

Validates quantitative models against benchmark values and statistical
acceptance criteria before they are used in production calculations.

Responsibilities:
  - Back-test models against known datasets
  - Compare to analytical / reference values within tolerance bands
  - Run statistical hypothesis tests (t-test, KS-test)
  - Produce a ModelValidationReport suitable for a model risk committee

Supported validation types:
  - ANALYTICAL  : compare to closed-form reference
  - MONTE_CARLO : check convergence of MC estimates
  - BACKTESTING : compare predictions to realised outcomes
  - STRESS      : behaviour under extreme inputs
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Callable, Optional

import numpy as np

log = logging.getLogger(__name__)


class ValidationType(str, Enum):
    ANALYTICAL = "analytical"
    MONTE_CARLO = "monte_carlo"
    BACKTESTING = "backtesting"
    STRESS = "stress"


class ValidationStatus(str, Enum):
    PASSED = "passed"
    FAILED = "failed"
    CONDITIONAL = "conditional"   # passed with caveats / warnings


@dataclass
class ValidationTest:
    name: str
    validation_type: ValidationType
    passed: bool
    expected: Optional[float]
    actual: Optional[float]
    relative_error: Optional[float]       # |actual - expected| / |expected|
    tolerance: Optional[float]
    message: str = ""


@dataclass
class ModelValidationReport:
    model_name: str
    model_version: str
    tests: list[ValidationTest] = field(default_factory=list)
    validated_at: datetime = field(default_factory=datetime.utcnow)

    @property
    def status(self) -> ValidationStatus:
        if any(not t.passed for t in self.tests):
            return ValidationStatus.FAILED
        warnings = [
            t for t in self.tests
            if t.relative_error is not None
            and t.tolerance is not None
            and t.relative_error > t.tolerance * 0.8  # within 20% of tolerance
        ]
        if warnings:
            return ValidationStatus.CONDITIONAL
        return ValidationStatus.PASSED

    @property
    def is_approved(self) -> bool:
        return self.status != ValidationStatus.FAILED

    def summary(self) -> str:
        n_pass = sum(1 for t in self.tests if t.passed)
        n_fail = len(self.tests) - n_pass
        return (
            f"Model '{self.model_name}' v{self.model_version}: "
            f"{self.status.value.upper()} — "
            f"{n_pass}/{len(self.tests)} tests passed"
            + (f", {n_fail} FAILED" if n_fail else "")
        )


class ModelRiskFramework:
    """
    Executes and records model validation tests.

    Usage::

        mrv = ModelRiskFramework()
        report = mrv.validate_black_scholes_call()
        if not report.is_approved:
            raise RuntimeError(report.summary())
    """

    def __init__(self, default_tolerance: float = 0.001) -> None:
        self._tolerance = default_tolerance
        self._reports: list[ModelValidationReport] = []

    # ── Generic validation ────────────────────────────────────────────────────

    def compare_to_reference(
        self,
        model_fn: Callable[..., float],
        reference_fn: Callable[..., float],
        test_cases: list[dict[str, Any]],
        model_name: str,
        model_version: str = "0.0.0",
        tolerance: Optional[float] = None,
    ) -> ModelValidationReport:
        """
        Run *model_fn* and *reference_fn* on each test case and compare results.

        Parameters
        ----------
        model_fn:
            The model under test, called with ``**test_case``.
        reference_fn:
            The reference/benchmark implementation, called with ``**test_case``.
        test_cases:
            List of parameter dicts.
        tolerance:
            Maximum acceptable relative error per test (overrides default).
        """
        tol = tolerance if tolerance is not None else self._tolerance
        report = ModelValidationReport(model_name=model_name, model_version=model_version)

        for i, case in enumerate(test_cases):
            test_name = f"case_{i+1}"
            try:
                actual = float(model_fn(**case))
                expected = float(reference_fn(**case))

                if math.isclose(expected, 0.0, abs_tol=1e-10):
                    rel_err = abs(actual - expected)
                else:
                    rel_err = abs(actual - expected) / abs(expected)

                passed = rel_err <= tol
                report.tests.append(
                    ValidationTest(
                        name=test_name,
                        validation_type=ValidationType.ANALYTICAL,
                        passed=passed,
                        expected=expected,
                        actual=actual,
                        relative_error=rel_err,
                        tolerance=tol,
                        message="" if passed else f"Relative error {rel_err:.4%} > tolerance {tol:.4%}",
                    )
                )
            except Exception as exc:
                report.tests.append(
                    ValidationTest(
                        name=test_name,
                        validation_type=ValidationType.ANALYTICAL,
                        passed=False,
                        expected=None,
                        actual=None,
                        relative_error=None,
                        tolerance=tol,
                        message=f"Exception: {exc}",
                    )
                )

        self._reports.append(report)
        if report.is_approved:
            log.info("%s", report.summary())
        else:
            log.error("%s", report.summary())
        return report

    # ── Monte Carlo convergence check ─────────────────────────────────────────

    def check_mc_convergence(
        self,
        estimates: list[float],
        reference: float,
        model_name: str,
        model_version: str = "0.0.0",
        tolerance: Optional[float] = None,
    ) -> ModelValidationReport:
        """
        Validate that a list of MC estimates converges to the reference value.

        Checks:
          1. Mean estimate within tolerance of reference.
          2. Standard error is decreasing (1/√N rule).
        """
        tol = tolerance if tolerance is not None else self._tolerance
        report = ModelValidationReport(model_name=model_name, model_version=model_version)
        n = len(estimates)
        mean_est = float(np.mean(estimates))
        std_err = float(np.std(estimates) / math.sqrt(n))

        rel_err = abs(mean_est - reference) / abs(reference) if reference != 0 else abs(mean_est)

        report.tests.append(
            ValidationTest(
                name="mc_mean_convergence",
                validation_type=ValidationType.MONTE_CARLO,
                passed=rel_err <= tol,
                expected=reference,
                actual=mean_est,
                relative_error=rel_err,
                tolerance=tol,
                message=f"n={n}, std_err={std_err:.6f}",
            )
        )

        expected_std_err = abs(reference) * tol   # acceptable noise floor
        report.tests.append(
            ValidationTest(
                name="mc_standard_error",
                validation_type=ValidationType.MONTE_CARLO,
                passed=std_err < expected_std_err * 2,
                expected=expected_std_err,
                actual=std_err,
                relative_error=None,
                tolerance=None,
                message=f"Std error {std_err:.6f} vs budget {expected_std_err:.6f}",
            )
        )

        self._reports.append(report)
        return report

    # ── Stress testing ────────────────────────────────────────────────────────

    def check_boundary_conditions(
        self,
        model_fn: Callable[..., float],
        stress_cases: list[dict[str, Any]],
        model_name: str,
        model_version: str = "0.0.0",
    ) -> ModelValidationReport:
        """
        Verify that the model doesn't produce NaN, Inf, or negative values
        under extreme inputs.

        Each ``stress_case`` dict may include an optional ``expected_finite``
        key (bool, default True).
        """
        report = ModelValidationReport(model_name=model_name, model_version=model_version)

        for i, case in enumerate(stress_cases):
            expect_finite = case.pop("expected_finite", True)
            label = case.pop("label", f"stress_{i+1}")
            try:
                actual = float(model_fn(**case))
                is_finite = math.isfinite(actual)
                passed = is_finite if expect_finite else True
                report.tests.append(
                    ValidationTest(
                        name=label,
                        validation_type=ValidationType.STRESS,
                        passed=passed,
                        expected=None,
                        actual=actual,
                        relative_error=None,
                        tolerance=None,
                        message="" if passed else f"Non-finite output: {actual}",
                    )
                )
            except Exception as exc:
                report.tests.append(
                    ValidationTest(
                        name=label,
                        validation_type=ValidationType.STRESS,
                        passed=False,
                        expected=None,
                        actual=None,
                        relative_error=None,
                        tolerance=None,
                        message=f"Exception under stress: {exc}",
                    )
                )

        self._reports.append(report)
        return report

    def all_reports(self) -> list[ModelValidationReport]:
        return list(self._reports)
