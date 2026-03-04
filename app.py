import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
import json
import re

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

# 1. 環境変数の読み込み
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 2. クライアントの初期化
# 前バージョンの genai.configure ではなく Client オブジェクトを作ります
client = genai.Client(api_key=api_key)

#食べ物以外を入力したとき＝0kcal
#複数の料理を入力したとき＝合算したkcal
def get_ai_calories(dish_name):
    """最新ライブラリを使用したカロリー推定"""
    prompt = f"""
    「{dish_name}」の1人前の推定カロリーを教えてください。
    必ず以下のJSON形式で回答してください。
    {{
      "calories": 数値のみ（単位なし）
    }}
    """
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt
    )

    st.write(f": {response.text} ")#AIの応答文チェック

    json_match = re.search(r'\{.*\}', response.text, re.DOTALL)

    if not json_match: #防御型プログラミングの例
        # ユーザーに状況を伝え、Noneを返して後続の処理をさせない
        st.error("AIから有効なデータが返ってきませんでした。もう一度試してください。")
        return None
    

    try:
        json_str = json_match.group()
        data = json.loads(json_str)
        calories = data["calories"]
        return calories
        
    except Exception as e:
        st.error(f"AI推定中にエラーが発生しました: {e}")
        st.write(f"結果: {response.text}")
        return None

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

    # --- 食事情報入力セクション---
    st.header("3. 食事情報の入力")

    # 朝食の有無
    breakfast = st.radio("朝食の有無を選択してください", ["食べた  ", "食べなかった"]) #後で朝食も計算式に入れるときに使う変数

    st.title("AI昼食カロリーチェッカー 🥗")

    dish_name = st.text_input("今日食べた昼食は何ですか？", placeholder="例：カツ丼、冷やし中華など")

    if st.button("AIでカロリーを推定する"):
        if dish_name:
            with st.spinner("AIが栄養素を解析中..."):
                result = get_ai_calories(dish_name)
                if result:
                    st.write(f"結果: {result} kcal")

        else:
            st.warning("料理名を入力してください！")





if __name__ == "__main__":
    main()