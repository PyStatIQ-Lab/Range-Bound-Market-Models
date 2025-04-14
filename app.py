import streamlit as st
import pandas as pd
import yfinance as yf
import ta

# Load Excel sheets
@st.cache_data
def load_excel_sheets(file):
    xls = pd.ExcelFile(file)
    return xls.sheet_names

# Download stock data
def fetch_stock_data(symbol):
    try:
        df = yf.download(symbol, period='3mo', interval='1d', progress=False)
        if df.empty:
            return None
        df.dropna(inplace=True)
        return df
    except Exception:
        return None

# Bollinger Bands Reversal Model
def bollinger_bands_signal(df):
    bb = ta.volatility.BollingerBands(close=df['Close'], window=20, window_dev=2)
    bb_high = bb.bollinger_hband().astype(float)
    bb_low = bb.bollinger_lband().astype(float)
    close = df['Close']

    if close.iloc[-1] < bb_low.iloc[-1]:
        return "Buy (Bollinger Reversal)"
    elif close.iloc[-1] > bb_high.iloc[-1]:
        return "Sell (Bollinger Reversal)"
    return None

# RSI Mean Reversion Model
def rsi_signal(df):
    rsi_series = ta.momentum.RSIIndicator(close=df['Close'], window=14).rsi()
    rsi_value = float(rsi_series.iloc[-1])
    if rsi_value < 30:
        return "Buy (RSI Mean Reversion)"
    elif rsi_value > 70:
        return "Sell (RSI Mean Reversion)"
    return None

# Stochastic Oscillator Model
def stochastic_signal(df):
    stoch = ta.momentum.StochasticOscillator(
        high=df['High'], low=df['Low'], close=df['Close'], window=14, smooth_window=3
    )
    k = stoch.stoch().astype(float)
    d = stoch.stoch_signal().astype(float)

    if k.iloc[-1] < 20 and d.iloc[-1] < 20:
        return "Buy (Stochastic)"
    elif k.iloc[-1] > 80 and d.iloc[-1] > 80:
        return "Sell (Stochastic)"
    return None

# Keltner Channel Reversal Model
def keltner_signal(df):
    kc = ta.volatility.KeltnerChannel(
        high=df['High'], low=df['Low'], close=df['Close'], window=20
    )
    upper = kc.keltner_channel_hband().astype(float)
    lower = kc.keltner_channel_lband().astype(float)
    close = df['Close']

    if close.iloc[-1] < lower.iloc[-1]:
        return "Buy (Keltner Reversal)"
    elif close.iloc[-1] > upper.iloc[-1]:
        return "Sell (Keltner Reversal)"
    return None

# Analyze a single stock
def analyze_stock(symbol):
    df = fetch_stock_data(symbol)
    if df is None:
        return None

    signals = []
    for model in [bollinger_bands_signal, rsi_signal, stochastic_signal, keltner_signal]:
        try:
            signal = model(df)
            if signal:
                signals.append(signal)
        except Exception as e:
            print(f"Error analyzing {symbol} with {model.__name__}: {e}")
            continue

    if signals:
        return {"Symbol": symbol, "Signals": signals}
    return None

# App UI
st.title("📊 Range-Bound Market Signal Analyzer")
st.write("This app analyzes stock tickers from an Excel sheet using reversal-based technical models.")

# Upload and select Excel sheet
excel_file = "stocklist.xlsx"
stock_sheets = load_excel_sheets(excel_file)
selected_sheet = st.selectbox("Select Stock List", stock_sheets)
analyze_button = st.button("Analyze Stocks")

# Main analysis logic
if analyze_button:
    try:
        stock_df = pd.read_excel(excel_file, sheet_name=selected_sheet)
        
        if 'Symbol' not in stock_df.columns:
            st.error("❌ Error: The selected sheet doesn't have a 'Symbol' column.")
        else:
            symbols = stock_df['Symbol'].dropna().tolist()
            results = []
            progress_bar = st.progress(0)
            status_text = st.empty()

            for i, symbol in enumerate(symbols):
                status_text.text(f"🔍 Analyzing {symbol} ({i+1}/{len(symbols)})...")
                result = analyze_stock(symbol)
                if result:
                    results.append(result)
                progress_bar.progress((i + 1) / len(symbols))

            if results:
                st.success(f"✅ Analysis complete. {len(results)} stocks with signals.")
                results_df = pd.DataFrame(results)
                results_df['Signals'] = results_df['Signals'].apply(lambda x: ", ".join(x))
                st.dataframe(results_df)
            else:
                st.warning("⚠️ No valid trading signals were found.")

    except Exception as e:
        st.error(f"Unexpected error: {e}")
