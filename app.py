from datetime import datetime
import os
import pandas as pd
import streamlit as st
import yfinance as yf

st.set_page_config(page_title="我的智慧資產管理系統", layout="wide")

# --- 歷史紀錄檔案設定 ---
HISTORY_FILE = "history.csv"


def load_history():
  if os.path.exists(HISTORY_FILE):
    return pd.read_csv(HISTORY_FILE)
  else:
    # 建立空的歷史紀錄 DataFrame
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
  # 如果今天已經記錄過了，就更新今天的數據；若沒有則新增一筆
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


# --- 介面標題 ---
st.title("💰 我的全方位淨資產儀表板 (含歷史趨勢)")
st.markdown("---")

# ================= 1. 側邊欄：自定義管理中心 =================
st.sidebar.header("⚙️ 自定義管理中心")

st.sidebar.subheader("➕ 新增銀行/資產帳戶")
new_asset_name = st.sidebar.text_input("帳戶名稱 (例: 玉山銀行)")
new_asset_val = st.sidebar.number_input(
    "初始金額", min_value=0, value=0, step=1000, key="new_asset_val"
)
if st.sidebar.button("新增資產帳戶"):
  if new_asset_name and new_asset_name not in st.session_state.custom_assets:
    st.session_state.custom_assets[new_asset_name] = new_asset_val
    st.sidebar.success(f"已新增 {new_asset_name}")
    st.rerun()

st.sidebar.subheader("➕ 新增負債項目")
new_liab_name = st.sidebar.text_input("負債名稱 (例: 其它信用卡)")
new_liab_val = st.sidebar.number_input(
    "負債金額", min_value=0, value=0, step=1000, key="new_liab_val"
)
if st.sidebar.button("新增負債項目"):
  if new_liab_name and new_liab_name not in st.session_state.custom_liabilities:
    st.session_state.custom_liabilities[new_liab_name] = new_liab_val
    st.sidebar.success(f"已新增 {new_liab_name}")
    st.rerun()

st.sidebar.markdown("---")

# ================= 2. 主畫面：各項數據計算 =================

# A. 資產計算 (現金 + 銀行)
st.subheader("💵 1. 現金與銀行資產")
col1, col2 = st.columns(2)

with col1:
  st.markdown("##### 實體錢包")
  st.session_state.cash_wallet = st.number_input(
      "錢包現金 (TWD)", value=st.session_state.cash_wallet, step=500
  )

with col2:
  st.markdown("##### 銀行帳戶")
  total_banks = 0
  for bank, val in list(st.session_state.custom_assets.items()):
    col_a, col_b = st.columns([3, 1])
    with col_a:
      st.session_state.custom_assets[bank] = st.number_input(
          f"{bank}", value=val, step=1000, key=f"bank_{bank}"
      )
    with col_b:
      if st.button("刪除", key=f"del_bank_{bank}"):
        del st.session_state.custom_assets[bank]
        st.rerun()
    total_banks += st.session_state.custom_assets[bank]

total_cash_assets = st.session_state.cash_wallet + total_banks
st.info(f"💡 現金與銀行資產總計：**$ {total_cash_assets:,.0f} 元**")

# B. 負債計算 (信用卡)
st.markdown("---")
st.subheader("💳 2. 負債項目 (信用卡等)")
total_liabilities = 0
for liab, val in list(st.session_state.custom_liabilities.items()):
  col_a, col_b = st.columns([3, 1])
  with col_a:
    st.session_state.custom_liabilities[liab] = st.number_input(
        f"{liab}", value=val, step=1000, key=f"liab_{liab}"
    )
  with col_b:
    if st.button("刪除", key=f"del_liab_{liab}"):
      del st.session_state.custom_liabilities[liab]
      st.rerun()
  total_liabilities += st.session_state.custom_liabilities[liab]

st.warning(f"⚠️ 負債總計：**$ {total_liabilities:,.0f} 元**")

# C. 權益計算 (股票自動抓取收盤價)
st.markdown("---")
st.subheader("📈 3. 權益項目 (台股自動更新市值)")

with st.expander("➕ 新增持股"):
  col_s1, col_s2, col_s3 = st.columns(3)
  with col_s1:
    s_code = st.text_input("台股代號 (例: 2330)", value="")
  with col_s2:
    s_name = st.text_input("股票簡稱 (例: 台積電)", value="")
  with col_s3:
    s_shares = st.number_input("持有股數", min_value=1, value=1000, step=100)

  if st.button("加入股票清單"):
    if s_code:
      formatted_code = s_code.strip()
      if not formatted_code.endswith(".TW"):
        formatted_code += ".TW"
      st.session_state.stocks.append(
          {"code": formatted_code, "name": s_name, "shares": s_shares}
      )
      st.success(f"已新增 {s_name}")
      st.rerun()

total_stock_equity = 0
stock_data_list = []

for stock in st.session_state.stocks:
  current_price = get_tw_stock_price(stock["code"])
  market_value = current_price * stock["shares"]
  total_stock_equity += market_value
  stock_data_list.append({
      "股票名稱": stock["name"],
      "代號": stock["code"],
      "股數": stock["shares"],
      "即時收盤價": current_price,
      "總市值": market_value,
  })

if stock_data_list:
  st.dataframe(pd.DataFrame(stock_data_list), use_container_width=True)

  stock_to_remove = st.selectbox(
      "選擇要刪除的股票",
      options=[s["name"] for s in st.session_state.stocks],
      key="remove_stock",
  )
  if st.button("確認刪除此股票"):
    st.session_state.stocks = [
        s for s in st.session_state.stocks if s["name"] != stock_to_remove
    ]
    st.rerun()

st.success(f"💡 股票權益總市值：**$ {total_stock_equity:,.0f} 元**")

# ================= 3. 總資產結算與自動記錄 =================
st.markdown("---")
st.header("🎯 總資產結算看板")

net_worth = total_cash_assets - total_liabilities + total_stock_equity

col_res1, col_res2, col_res3, col_res4 = st.columns(4)
col_res1.metric("＋ 總資產 (現金+銀行)", f"$ {total_cash_assets:,.0f}")
col_res2.metric("－ 負債 (信用卡)", f"$ {total_liabilities:,.0f}")
col_res3.metric("＋ 權益 (台股市值)", f"$ {total_stock_equity:,.0f}")
col_res4.metric("✨ 最終淨資產", f"$ {net_worth:,.0f}")

# 自動儲存今日數據到歷史紀錄
today_date = datetime.now().strftime("%Y-%m-%d")
today_record = {
    "Date": today_date,
    "Total_Assets": total_cash_assets + total_stock_equity,
    "Cash_Banks": total_cash_assets,
    "Stock_Equity": total_stock_equity,
    "Liabilities": total_liabilities,
    "Net_Worth": net_worth,
}
save_history(today_record)

# ================= 4. 歷史趨勢折線圖區塊 =================
st.markdown("---")
st.header("📈 財富與負債歷史趨勢圖")

history_df = load_history()

if not history_df.empty:
  # 確保 Date 是日期格式並排序
  history_df["Date"] = pd.to_datetime(history_df["Date"])
  history_df = history_df.sort_values("Date")

  tab1, tab2, tab3, tab4 = st.tabs([
      "✨ 總資產 (淨資產) 每日趨勢",
      "💵 資產 (現金+銀行) 每日趨勢",
      "📈 股票權益 每日趨勢",
      "💳 負債 (信用卡) 每月趨勢",
  ])

  with tab1:
    st.subheader("總資產 (Net Worth) 每日走勢")
    st.line_chart(
        history_df.set_index("Date")[["Net_Worth"]], color="#29b5e8"
    )

  with tab2:
    st.subheader("資產 (現金與銀行) 每日走勢")
    st.line_chart(
        history_df.set_index("Date")[["Cash_Banks"]], color="#00C853"
    )

  with tab3:
    st.subheader("股票權益 (台股市值) 每日走勢")
    st.line_chart(
        history_df.set_index("Date")[["Stock_Equity"]], color="#FFAB00"
    )

  with tab4:
    st.subheader("負債 (信用卡) 每月趨勢平均")
    # 轉換成每月平均（取每個月的最後一筆或平均值）
    history_df["YearMonth"] = history_df["Date"].dt.to_period("M")
    monthly_liab = (
        history_df.groupby("YearMonth")["Liabilities"].mean().reset_index()
    )
    monthly_liab["YearMonth"] = monthly_liab["YearMonth"].astype(str)
    st.line_chart(
        monthly_liab.set_index("YearMonth")[["Liabilities"]], color="#FF5252"
    )
else:
  st.info("目前尚無歷史數據，系統已為您記錄今天的第一筆資料！明天打開就會有折線圖了。")
