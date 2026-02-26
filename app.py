import streamlit as st

# 活動係数の定義
activity_map = {
    "ほぼ運動しない (デスクワーク中心)": 1.2,
    "軽い運動 (週1〜3回程度)": 1.375,
    "中程度の運動 (週3〜5回程度)": 1.55,
    "激しい運動 (週6〜7回程度)": 1.725,
    "非常に激しい運動 (プロアスリート並み)": 1.9
}

# --- 計算ロジック ---
# ハリス・ベネディクト方程式によるBMR（基礎代謝量）の計算
# 数字は定数
def calculate_bmr(gender, weight, height, age):
    if gender == "男性":
        bmr = 13.397 * weight + 4.799 * height - 5.677 * age + 88.362
    else:
        bmr = 9.247 * weight + 3.098 * height - 4.33 * age + 447.593

    return bmr
   
def main():
    # アプリのタイトル
    st.title("🥗 一日の推奨カロリー計算")
    st.write("あなたの基本情報を入力するだけで、1日に必要な推定エネルギー量を計算します。")

    # --- 入力セクション ---
    st.header("1. 基本情報の入力")

    # 性別を選択
    gender = st.radio("性別を選択してください", ["男性", "女性"])

    # 数値の入力
    col1, col2, col3 = st.columns(3)
    with col1:
        age = st.number_input("年齢", min_value=0, max_value=120, value=25)
    with col2:
        height = st.number_input("身長 (cm)", min_value=50.0, max_value=250.0, value=170.0, step=0.1, format="%.1f")
    with col3:
        weight = st.number_input("体重 (kg)", min_value=10.0, max_value=300.0, value=65.0, step=0.1, format="%.1f")

    # 活動レベルの選択
    activity_level = st.selectbox(
        "日中の活動レベルを選択してください",
        [
            "ほぼ運動しない (デスクワーク中心)",
            "軽い運動 (週1〜3回程度)",
            "中程度の運動 (週3〜5回程度)",
            "激しい運動 (週6〜7回程度)",
            "非常に激しい運動 (プロアスリート並み)"
        ]
    )

    # --- 計算 ---
    bmr = calculate_bmr(gender, weight, height, age)
    tdee = bmr * activity_map[activity_level]# TDEE（1日の総消費エネルギー量）

    # --- 結果表示セクション ---
    st.divider()
    st.header("2. 計算結果")

    st.metric(label="あなたの基礎代謝量 (BMR)", value=f"{int(bmr)} kcal")
    st.success(f"あなたの1日の推定メンテナンスカロリー (TDEE) は **{int(tdee)} kcal** です！")

    st.info("※この数値は目安です。実際の体調や目的に合わせて調整してください。")

if __name__ == "__main__":
    main()