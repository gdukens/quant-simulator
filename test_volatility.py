"""
Week 8: Volatility surface smoke tests.
"""

import numpy as np
import pandas as pd
import pytest

from quantlib_pro.volatility import (
    VolatilitySurface,
    build_surface_from_prices,
    interpolate_surface,
    extract_volatility_slice,
    compute_volatility_skew,
    compute_volatility_smile_curvature,
    SVIParameters,
    svi_total_variance,
    svi_implied_vol,
    fit_svi_smile,
    SABRParameters,
    sabr_implied_vol,
    fit_sabr_smile,
    polynomial_smile,
)


def test_surface_construction():
    """Test volatility surface construction from option prices."""
    # Synthetic option prices
    spot = 100.0
    r = 0.05
    
    strikes = [90, 95, 100, 105, 110]
    maturities = [0.25, 0.5, 1.0]
    
    data = []
    for T in maturities:
        for K in strikes:
            # Generate synthetic Black-Scholes price
            # Use a simple smile: higher vol for OTM
            moneyness = K / spot
            base_vol = 0.20
            vol = base_vol + 0.05 * (moneyness - 1.0) ** 2
            
            # Price call using BS formula (simplified)
            from quantlib_pro.options import price_call
            price = price_call(spot, K, T, r, vol)
            
            data.append({
                'strike': K,
                'maturity': T,
                'price': price,
                'option_type': 'call',
            })
    
    df = pd.DataFrame(data)
    
    # Build surface
    surface = build_surface_from_prices(df, spot, r)
    
    # Verify surface has points
    assert len(surface.points) > 0
    assert surface.spot_price == spot
    assert surface.risk_free_rate == r
    
    # Convert to dataframe
    surface_df = surface.to_dataframe()
    assert len(surface_df) == len(surface.points)
    assert 'strike' in surface_df.columns
    assert 'implied_vol' in surface_df.columns


def test_surface_interpolation():
    """Test volatility surface interpolation."""
    from quantlib_pro.volatility.surface import SurfacePoint
    
    # Create simple surface
    points = [
        SurfacePoint(strike=95, maturity=0.5, implied_vol=0.22, moneyness=0.95, option_type='call', market_price=5.0),
        SurfacePoint(strike=100, maturity=0.5, implied_vol=0.20, moneyness=1.0, option_type='call', market_price=7.0),
        SurfacePoint(strike=105, maturity=0.5, implied_vol=0.23, moneyness=1.05, option_type='call', market_price=4.0),
        SurfacePoint(strike=95, maturity=1.0, implied_vol=0.24, moneyness=0.95, option_type='call', market_price=8.0),
        SurfacePoint(strike=100, maturity=1.0, implied_vol=0.22, moneyness=1.0, option_type='call', market_price=10.0),
        SurfacePoint(strike=105, maturity=1.0, implied_vol=0.25, moneyness=1.05, option_type='call', market_price=7.0),
    ]
    
    surface = VolatilitySurface(points=points, spot_price=100.0, risk_free_rate=0.05, timestamp=0.0)
    
    # Test RBF interpolation
    interp_func = interpolate_surface(surface, method='rbf')
    
    # Interpolate at known point
    vol_100_05 = interp_func(100.0, 0.5)
    assert 0.15 < vol_100_05 < 0.30
    
    # Test linear interpolation
    interp_linear = interpolate_surface(surface, method='linear')
    vol_100_05_linear = interp_linear(100.0, 0.5)
    assert 0.15 < vol_100_05_linear < 0.30


def test_volatility_slice():
    """Test extracting volatility smile for a specific maturity."""
    from quantlib_pro.volatility.surface import SurfacePoint
    
    points = [
        SurfacePoint(strike=95, maturity=0.5, implied_vol=0.22, moneyness=0.95, option_type='call', market_price=5.0),
        SurfacePoint(strike=100, maturity=0.5, implied_vol=0.20, moneyness=1.0, option_type='call', market_price=7.0),
        SurfacePoint(strike=105, maturity=0.5, implied_vol=0.23, moneyness=1.05, option_type='call', market_price=4.0),
        SurfacePoint(strike=95, maturity=1.0, implied_vol=0.24, moneyness=0.95, option_type='call', market_price=8.0),
    ]
    
    surface = VolatilitySurface(points=points, spot_price=100.0, risk_free_rate=0.05, timestamp=0.0)
    
    # Extract 6-month smile
    smile_df = extract_volatility_slice(surface, maturity=0.5, tolerance=0.1)
    
    assert len(smile_df) == 3
    assert all(smile_df['strike'].isin([95, 100, 105]))


def test_volatility_skew():
    """Test volatility skew calculation."""
    from quantlib_pro.volatility.surface import SurfacePoint
    
    # Downward sloping smile (negative skew)
    points = [
        SurfacePoint(strike=90, maturity=0.5, implied_vol=0.30, moneyness=0.90, option_type='put', market_price=5.0),
        SurfacePoint(strike=100, maturity=0.5, implied_vol=0.20, moneyness=1.0, option_type='call', market_price=7.0),
        SurfacePoint(strike=110, maturity=0.5, implied_vol=0.15, moneyness=1.10, option_type='call', market_price=4.0),
    ]
    
    surface = VolatilitySurface(points=points, spot_price=100.0, risk_free_rate=0.05, timestamp=0.0)
    smile_df = extract_volatility_slice(surface, maturity=0.5, tolerance=0.1)
    
    skew = compute_volatility_skew(smile_df)
    
    # Skew should be negative
    assert skew < 0


def test_volatility_curvature():
    """Test volatility smile curvature."""
    from quantlib_pro.volatility.surface import SurfacePoint
    
    # U-shaped smile (positive curvature)
    points = [
        SurfacePoint(strike=90, maturity=0.5, implied_vol=0.25, moneyness=0.90, option_type='put', market_price=5.0),
        SurfacePoint(strike=100, maturity=0.5, implied_vol=0.20, moneyness=1.0, option_type='call', market_price=7.0),
        SurfacePoint(strike=110, maturity=0.5, implied_vol=0.25, moneyness=1.10, option_type='call', market_price=4.0),
    ]
    
    surface = VolatilitySurface(points=points, spot_price=100.0, risk_free_rate=0.05, timestamp=0.0)
    smile_df = extract_volatility_slice(surface, maturity=0.5, tolerance=0.1)
    
    curvature = compute_volatility_smile_curvature(smile_df)
    
    # Curvature should be positive
    assert curvature > 0


def test_svi_model():
    """Test SVI parametric model."""
    params = SVIParameters(a=0.04, b=0.1, rho=-0.3, m=0.0, sigma=0.2)
    
    # Total variance at ATM
    w_atm = svi_total_variance(0.0, params)
    assert w_atm > 0
    
    # IV for 1-year maturity
    iv_atm = svi_implied_vol(0.0, T=1.0, params=params)
    assert 0.1 < iv_atm < 0.5


def test_fit_svi():
    """Test SVI fitting to synthetic smile."""
    # Generate synthetic smile
    log_m = np.array([-0.2, -0.1, 0.0, 0.1, 0.2])
    true_params = SVIParameters(a=0.04, b=0.1, rho=-0.2, m=0.0, sigma=0.15)
    T = 0.5
    
    true_vols = np.array([svi_implied_vol(k, T, true_params) for k in log_m])
    
    # Fit model
    fitted_params = fit_svi_smile(log_m, true_vols, T)
    
    # Check fitted vols are close
    fitted_vols = np.array([svi_implied_vol(k, T, fitted_params) for k in log_m])
    
    assert np.allclose(true_vols, fitted_vols, rtol=0.1)


def test_sabr_model():
    """Test SABR parametric model."""
    params = SABRParameters(alpha=0.20, beta=0.5, rho=-0.3, nu=0.4)
    
    # IV at ATM
    iv = sabr_implied_vol(K=100, F=100, T=1.0, params=params)
    # SABR ATM approximation: α / F^(1-β)
    expected_atm = params.alpha / (100 ** (1 - params.beta))
    assert abs(iv - expected_atm) < 0.01
    
    # IV OTM
    iv_otm = sabr_implied_vol(K=110, F=100, T=1.0, params=params)
    assert iv_otm > 0


def test_fit_sabr():
    """Test SABR fitting to synthetic smile."""
    F = 100.0
    T = 0.5
    strikes = np.array([90, 95, 100, 105, 110])
    
    # Generate synthetic vols (monotonic smile)
    true_vols = 0.20 + 0.01 * np.abs(strikes - F) / F
    
    # Fit SABR
    fitted_params = fit_sabr_smile(strikes, true_vols, F, T, beta=0.5)
    
    # Check fitted vols
    fitted_vols = np.array([sabr_implied_vol(K, F, T, fitted_params) for K in strikes])
    
    # Should be reasonably close
    assert np.allclose(true_vols, fitted_vols, atol=0.05)


def test_polynomial_smile():
    """Test polynomial smile model."""
    moneyness = np.array([0.9, 0.95, 1.0, 1.05, 1.1])
    vols = polynomial_smile(moneyness, atm_vol=0.20, skew=-0.1, curvature=0.05)
    
    assert len(vols) == len(moneyness)
    # ATM vol should be close to input
    atm_idx = 2
    assert abs(vols[atm_idx] - 0.20) < 0.01


def test_get_atm_vol():
    """Test ATM volatility extraction."""
    from quantlib_pro.volatility.surface import SurfacePoint
    
    points = [
        SurfacePoint(strike=95, maturity=0.5, implied_vol=0.22, moneyness=0.95, option_type='call', market_price=5.0),
        SurfacePoint(strike=100, maturity=0.5, implied_vol=0.20, moneyness=1.0, option_type='call', market_price=7.0),
        SurfacePoint(strike=105, maturity=0.5, implied_vol=0.23, moneyness=1.05, option_type='call', market_price=4.0),
    ]
    
    surface = VolatilitySurface(points=points, spot_price=100.0, risk_free_rate=0.05, timestamp=0.0)
    
    atm_vol = surface.get_atm_vol(maturity=0.5)
    
    # Should be close to 0.20
    assert abs(atm_vol - 0.20) < 0.05


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
