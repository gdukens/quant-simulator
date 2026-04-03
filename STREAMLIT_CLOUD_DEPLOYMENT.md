#  QuantLib Pro - Streamlit Community Cloud Deployment

Deploy your QuantLib Pro quantitative finance platform to **Streamlit Community Cloud** for free!

##  Prerequisites

1. **GitHub Account** - Your code needs to be in a GitHub repository
2. **Streamlit Community Cloud Account** - Sign up at [share.streamlit.io](https://share.streamlit.io)
3. **API Keys** (Optional but recommended):
   - **FRED API Key** - Get from [Federal Reserve](https://fred.stlouisfed.org/docs/api/api_key.html) (FREE)
   - **Alpha Vantage API Key** - Get from [Alpha Vantage](https://www.alphavantage.co/support/#api-key) (FREE tier available)

##  Deployment Steps

### 1. Push to GitHub

```bash
# Commit all changes
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### 2. Deploy to Streamlit Community Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with your GitHub account
3. Click **"New app"**
4. Select your repository: `your-username/quantlib-pro`
5. Set **Main file path**: `streamlit_app.py`
6. Click **"Deploy!"**

### 3. Configure Secrets (Optional)

In your Streamlit app dashboard:

1. Click the ** Settings** button
2. Go to **"Secrets"** tab
3. Add your API keys in TOML format:

```toml
# Secrets for QuantLib Pro
FRED_API_KEY = "your_fred_api_key_here"
ALPHA_VANTAGE_API_KEY = "your_alpha_vantage_key_here"
ALPHA_VANTAGE_ENABLED = "true"
APP_ENV = "production"
DEBUG = "false"
```

##  What Works in Cloud Mode

 **Core Features Available:**
- Portfolio optimization & risk analysis
- Market regime detection
- Volatility surface modeling  
- Options pricing (Black-Scholes, Binomial)
- Backtesting framework
- Real-time data from Yahoo Finance
- FRED economic data (with API key)
- Alpha Vantage market data (with API key)

 **All 30+ Quantitative Tools:**
- No database required for core functionality
- Graceful degradation when services unavailable
- Professional UI with Material Design icons

##  Your Deployed App

Once deployed, your app will be available at:
```
https://your-app-name.streamlit.app
```

##  Custom Domain (Optional)

For a custom domain:
1. Upgrade to Streamlit for Teams
2. Configure DNS settings
3. Add SSL certificate

##  Local Development

To run locally:
```bash
pip install -r requirements.txt
streamlit run streamlit_app.py
```

## 🆘 Troubleshooting

**Issue: App won't start**
- Check that `streamlit_app.py` is in the root directory
- Verify `requirements.txt` contains all dependencies

**Issue: Missing data**
- Add API keys to Streamlit secrets
- Check API key format in Settings page

**Issue: Slow performance**
- Streamlit Community Cloud has resource limits
- Consider optimizing data loading and caching

##  Support

- **Documentation**: Check individual page documentation
- **Issues**: Create GitHub issue in your repository
- **Community**: Streamlit Community Forum

---

** Congratulations! Your QuantLib Pro platform is now deployed and accessible worldwide!**