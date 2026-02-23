"""
Volatility surface and term structure analysis.
"""

from quantlib_pro.volatility.surface import (
    SurfacePoint,
    VolatilitySurface,
    build_surface_from_prices,
    interpolate_surface,
    extract_volatility_slice,
    compute_volatility_skew,
    compute_volatility_smile_curvature,
)
from quantlib_pro.volatility.smile_models import (
    SVIParameters,
    SABRParameters,
    svi_total_variance,
    svi_implied_vol,
    fit_svi_smile,
    sabr_implied_vol,
    fit_sabr_smile,
    polynomial_smile,
)

__all__ = [
    # Surface construction
    "SurfacePoint",
    "VolatilitySurface",
    "build_surface_from_prices",
    "interpolate_surface",
    "extract_volatility_slice",
    "compute_volatility_skew",
    "compute_volatility_smile_curvature",
    # Parametric models
    "SVIParameters",
    "SABRParameters",
    "svi_total_variance",
    "svi_implied_vol",
    "fit_svi_smile",
    "sabr_implied_vol",
    "fit_sabr_smile",
    "polynomial_smile",
]
