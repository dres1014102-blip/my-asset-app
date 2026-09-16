from datetime import datetime
import os
import pandas as pd
import streamlit as st
import yfinance as yf

# 頁面基本設定 (手機版優先優化)
st.set_page_config(
    page_title="我的智慧資產管理系統", page_icon="💰", layout="centered"
)

# --- 注入精美 CSS (改善字體、卡片設計、按鈕與間距) ---
st.markdown(
    """
    <style>
    /* 全局字體與背景微調 */
    .stApp {
        background-color: #f8f9fa;
    }
    
    /* 標題與文字調整 */
    h1 {
        font-size: 26px !important;
        font-weight: 700 !important;
        color: #1f2937 !important;
        margin-bottom: 0px !important;
    }
    h2, h3 {
        color: #374151 !important;
        font-weight: 600 !important;
    }
    
    /* 卡片區塊容器風格 */
    .metric-card {
        background-color: white;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        margin-bottom: 12px;
        border: 1px solid #e5e7eb;
    }
    
    /* 調整輸入框標籤字體大小 */
    label {
        font-size: 14px !important;
        font-weight: 500 !important;
        color: #4b5563 !important;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- 歷史紀錄檔案設定 ---
HISTORY_FILE = "history.csv"


def load_history():
  if os.path.exists(HISTORY_FILE):
    return pd.read_csv(HISTORY_FILE)
  else:
    return pd.DataFrame(
        columns=[
            "Date",
            "Total_Assets",
            "Cash_Banks",
            "Stock_Equity",
            "Liabilities",
            "Net_Worth",
        ]
    )


def save_history(data_row):
  df = load_history()
  today_str = data_row["Date"]
  if not df.empty and today_str in df["Date"].values:
    df.loc[df["Date"] == today_str, :] = list(data_row.values())
  else:
    df = pd.concat([df, pd.DataFrame([data_row])], ignore_index=True)
  df.to_csv(HISTORY_FILE, index=False)


# --- 初始化 Session State ---
if "cash_wallet" not in st.session_state:
  st.session_state.cash_wallet = 3000
if "custom_assets" not in st.session_state:
  st.session_state.custom_assets = {
      "中國信託": 50000,
      "國泰世華": 30000,
      "LINE Bank": 20000,
  }
if "custom_liabilities" not in st.session_state:
  st.session_state.custom_liabilities = {"國泰世華信用卡": 12000}
if "stocks" not in st.session_state:
  st.session_state.stocks = [
      {"code": "2330.TW", "name": "台積電", "shares": 1000},
      {"code": "2454.TW", "name": "聯發科", "shares": 500},
  ]


# --- 取得台股收盤價函數 ---
def get_tw_stock_price(stock_code):
  try:
    ticker = yf.Ticker(stock_code)
    todays_data = ticker.history(period="1d")
    if not todays_data.empty:
      return round(todays_data["Close"].iloc[-1], 2)
  except Exception:
    pass
  return 0.0


# --- 主介面標題 ---
st.title("💰 我的淨資產管理 App")
st.caption("✨ 每天自動更新台股市值與財富趨勢")
st.markdown("---")

# ================= 1. 頂部：核心數據總覽看板 =================
# 先計算各項數值以供總覽顯示
total_banks = sum(st.session_state.custom_assets.values())
total_cash_assets = st.session_state.cash_wallet + total_banks
total_liabilities = sum(st.session_state.custom_liabilities.values())

total_stock_equity = 0
for stock in st.session_state.stocks:
  current_price = get_tw_stock_price(stock["code"])
  total_stock_equity += current_price * stock["shares"]

net_worth = total_cash_assets - total_liabilities + total_stock_equity

# 使用美化卡片呈現最終淨資產
st.markdown(
    f"""
    <div style="background: linear-gradient(135deg, #2563eb, #1d4ed8); padding: 20px; border-radius: 16px; color: white; text-align: center; margin-bottom: 20px; box-shadow: 0 4px 12px rgba(37,99,235,0.2);">
        <div style="font-size: 14px; opacity: 0.9; letter-spacing: 1px;">目前淨資產 (Net Worth)</div>
        <div style="font-size: 32px; font-weight: 700; margin: 8px 0;">$ {net_worth:,.0f}</div>
        <div style="font-size: 12px; opacity: 0.8;">公式：資產 ($ {total_cash_assets:,.0f}) － 負債 ($ {total_liabilities:,.0f}) ＋ 權益 ($ {total_stock_equity:,.0f})</div>
    </div>
""",
    unsafe_allow_html=True,
)

# 自動儲存今日數據
today_date = datetime.now().strftime("%Y-%m-%d")
save_history({
    "Date": today_date,
    "Total_Assets": total_cash_assets + total_stock_equity,
    "Cash_Banks": total_cash_assets,
    "Stock_Equity": total_stock_equity,
    "Liabilities": total_liabilities,
    "Net_Worth": net_worth,
})


# ================= 2. 分頁設計 (讓介面變得非常直覺、不擁擠) =================
tab_main, tab_history, tab_settings = st.tabs(
    ["📝 資產明細與記帳", "📈 財富歷史折線圖", "⚙️ 新增與管理帳戶"]
)

with tab_main:
  st.markdown("### 💵 現金與銀行帳戶")
  st.session_state.cash_wallet = st.number_input(
      "👛 實體錢包現金 (TWD)",
      value=st.session_state.cash_wallet,
      step=500,
      format="%d",
  )

  for bank, val in list(st.session_state.custom_assets.items()):
    st.session_state.custom_assets[bank] = st.number_input(
        f"🏦 {bank}", value=val, step=1000, format="%d", key=f"main_bank_{bank}"
    )

  st.markdown("---")
  st.markdown("### 💳 信用卡負債")
  for liab, val in list(st.session_state.custom_liabilities.items()):
    st.session_state.custom_liabilities[liab] = st.number_input(
        f"💳 {liab}", value=val, step=1000, format="%d", key=f"main_liab_{liab}"
    )

  st.markdown("---")
  st.markdown("### 📈 股票權益 (自動抓取收盤價)")
  stock_data_list = []
  for stock in st.session_state.stocks:
    current_price = get_tw_stock_price(stock["code"])
    market_value = current_price * stock["shares"]
    stock_data_list.append({
        "股票名稱": stock["name"],
        "代號": stock["code"],
        "股數": stock["shares"],
        "即時收盤價": current_price,
        "總市值": market_value,
    })

  if stock_data_list:
    st.dataframe(pd.DataFrame(stock_data_list), use_container_width=True)


with tab_history:
  st.markdown("### 📊 財富與負債歷史趨勢")
  history_df = load_history()

  if not history_df.empty:
    history_df["Date"] = pd.to_datetime(history_df["Date"])
    history_df = history_df.sort_values("Date")

    chart_choice = st.selectbox(
        "選擇要查看的圖表項目", [
            "✨ 總資產 (淨資產) 每日趨勢",
            "💵 資產 (現金+銀行) 每日趨勢",
            "📈 股票權益 每日趨勢",
            "💳 負債 (信用卡) 每月趨勢",
        ]
    )

    if "總資產" in chart_choice:
      st.line_chart(
          history_df.set_index("Date")[["Net_Worth"]], color="#2563eb"
      )
    elif "資產" in chart_choice:
      st.line_chart(
          history_df.set_index("Date")[["Cash_Banks"]], color="#16a34a"
      )
    elif "股票" in chart_choice:
      st.line_chart(
          history_df.set_index("Date")[["Stock_Equity"]], color="#d97706"
      )
    elif "負債" in chart_choice:
      history_df["YearMonth"] = history_df["Date"].dt.to_period("M")
      monthly_liab = (
          history_df.groupby("YearMonth")["Liabilities"].mean().reset_index()
      )
      monthly_liab["YearMonth"] = monthly_liab["YearMonth"].astype(str)
      st.line_chart(
          monthly_liab.set_index("YearMonth")[["Liabilities"]], color="#dc2626"
      )
  else:
    st.info("尚無歷史數據，明天打開就會有折線圖囉！")


with tab_settings:
  st.markdown("### ⚙️ 新增或刪除帳戶與持股")

  with st.expander("➕ 新增銀行帳戶"):
    new_bank = st.text_input("銀行名稱 (例: 玉山銀行)")
    new_bank_val = st.number_input(
        "初始金額", min_value=0, value=0, step=1000, key="nb_val"
    )
    if st.button("確認新增銀行"):
      if new_bank and new_bank not in st.session_state.custom_assets:
        st.session_state.custom_assets[new_bank] = new_bank_val
        st.success(f"已新增 {new_bank}")
        st.rerun()

    if st.session_state.custom_assets:
      del_bank = st.selectbox(
          "選擇要刪除的銀行", list(st.session_state.custom_assets.keys())
      )
      if st.button("刪除此銀行帳戶"):
        del st.session_state.custom_assets[del_bank]
        st.rerun()

  with st.expander("➕ 新增信用卡負債"):
    new_liab = st.text_input("負債名稱 (例: 台新信用卡)")
    new_liab_val = st.number_input(
        "負債金額", min_value=0, value=0, step=1000, key="nl_val"
    )
    if st.button("確認新增負債"):
      if new_liab and new_liab not in st.session_state.custom_liabilities:
        st.session_state.custom_liabilities[new_liab] = new_liab_val
        st.success(f"已新增 {new_liab}")
        st.rerun()

    if st.session_state.custom_liabilities:
      del_liab = st.selectbox(
          "選擇要刪除的負債", list(st.session_state.custom_liabilities.keys())
      )
      if st.button("刪除此負債項目"):
        del st.session_state.custom_liabilities[del_liab]
        st.rerun()

  with st.expander("➕ 新增台股持股"):
    s_code = st.text_input("台股代號 (例: 2330 或 2330.TW)")
    s_name = st.text_input("股票簡稱 (例: 台積電)")
    s_shares = st.number_input(
        "持有股數", min_value=1, value=1000, step=100, key="s_sh"
    )
    if st.button("確認新增持股"):
      if s_code:
        f_code = s_code.strip()
        if not f_code.endswith(".TW"):
          f_code += ".TW"
        st.session_state.stocks.append(
            {"code": f_code, "name": s_name, "shares": s_shares}
        )
        st.success(f"已新增 {s_name}")
        st.rerun()

    if st.session_state.stocks:
      del_stock = st.selectbox(
          "選擇要刪除的股票", [s["name"] for s in st.session_state.stocks]
      )
      if st.button("刪除此股票"):
        st.session_state.stocks = [
            s for s in st.session_state.stocks if s["name"] != del_stock
        ]
        st.rerun()
