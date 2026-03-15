import streamlit as st
import os
from dotenv import load_dotenv
from google import genai
import json
import re
from PIL import Image

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
        result = 13.397 * weight + 4.799 * height - 5.677 * age + 88.362
    else:
        result = 9.247 * weight + 3.098 * height - 4.33 * age + 447.593

    return result

#朝食のカロリーを計算
DEFAULT_BREAKFAST_KCAL = 500

def breakfast_check(breakfast):
    if breakfast == "食べた":
        return DEFAULT_BREAKFAST_KCAL
    else:
        return 0

# 1. 環境変数の読み込み
load_dotenv()
api_key = os.getenv("GOOGLE_API_KEY")

# 2. クライアントの初期化
# 前バージョンの genai.configure ではなく Client オブジェクトを作ります
client = genai.Client(api_key=api_key) # 名前の重複

#食べ物以外を入力したとき＝0kcal
#複数の料理を入力したとき＝合算したkcal
def get_lunch_kcal(dish_name, uploaded_file):

    prompt = f"""
    料理名: {dish_name}
    指示:
    「{dish_name}」の1人前の推定カロリーを教えてください。
    必ず以下のJSON形式で回答してください。
    {{
      "calories": 数値のみ（単位なし）
    }}
    """
    # payloadに初期値として料理名を追加
    payload = [prompt]

    if uploaded_file is not None:
         # リストpayloadに最適化された画像を追加(append)
        payload.append(preprocess_image(uploaded_file,max_size=512))
        payload[0] += "画像も参考にして、より正確に推定してください。"   # プロンプトも追加 

    # 返ってきた応答をresponseに格納
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=payload
    )


    json_match = re.search(r'\{.*\}', response.text, re.DOTALL) #

    # ユーザーに状況を伝え、Noneを返して後続の処理をさせないやつ⇒防御型プログラミングの例
    if not json_match: 
        
        st.error("AIから有効なデータが返ってきませんでした。もう一度試してください。")
        return None
    

    try:
        json_str = json_match.group()
        result = json.loads(json_str)

        return int(result["calories"])
        
    except Exception as e:
        st.error(f"AI推定中にエラーが発生しました: {e}")
        st.write(f"結果: {response.text}")
        return None
    
# geminiに渡すために画像を軽くする処理。縦横サイズの最大値を512とした。
def preprocess_image(uploaded_file,max_size=512):
    # geminiが読み取れるようオブジェクトとして展開
    optimized_dish_img = Image.open(uploaded_file)
    # 画像サイズの最大値を設定し解像度を落とす⇒thumbnail((縦,横)) 
    optimized_dish_img.thumbnail((max_size,max_size)) 

    return optimized_dish_img # 最適化されたファイルを返す


#夕食の推奨カロリー計算
def calculate_dinner_kcal(tdee, breakfast_kcal, lunch_kcal):
    result = tdee - breakfast_kcal - lunch_kcal

    return int(result)




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
        height = st.number_input("身長 (cm)", min_value=50.0, max_value=250.0, value=170.0, step=0.5, format="%.1f")
    with col3:
        weight = st.number_input("体重 (kg)", min_value=10.0, max_value=300.0, value=65.0, step=0.5, format="%.1f")

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
    tdee = int(bmr * activity_map[activity_level])# TDEE（1日の総消費エネルギー量）

    # --- 結果表示セクション ---
    st.divider()
    st.header("2. 計算結果")

    st.metric(label="あなたの基礎代謝量 (BMR)", value=f"{int(bmr)} kcal")
    st.success(f"あなたの1日の推定メンテナンスカロリー (TDEE) は **{tdee} kcal** です！")

    st.info("※この数値は目安です。実際の体調や目的に合わせて調整してください。")

    # --- 食事情報入力セクション---
    st.header("3. 食事情報の入力")


    # 朝食の有無
    breakfast = st.radio("朝食の有無を選択してください", ["食べた", "食べなかった"]) #後で朝食も計算式に入れるときに使う変数
    breakfast_kcal = breakfast_check(breakfast)

    st.title("AI昼食カロリーチェッカー 🥗")

    dish_name = st.text_input("今日食べた昼食は何ですか？（必須項目）", placeholder="例：カツ丼、冷やし中華など")
    

    # ユーザーからの画像を受け取る
    uploaded_file = st.file_uploader("料理の写真をアップロードしてください（任意項目）", type=["jpg", "jpeg", "png"])

    if uploaded_file is not None:

        st.image(uploaded_file, caption="アップロードされた画像", width="stretch")


    # AIにプロンプト（あれば画像も）を処理させるボタン
    if st.button("AIでカロリーを推定する", disabled=not dish_name):
        
        with st.spinner("AIが栄養素を解析中..."):
            lunch_kcal = get_lunch_kcal(dish_name, uploaded_file)
        
        if lunch_kcal:
            st.success(f"昼食の推定カロリーは: {lunch_kcal} kcalです")
            dinner_kcal = calculate_dinner_kcal(tdee, breakfast_kcal, lunch_kcal)
            st.success(f"夕食の推奨カロリーは: {dinner_kcal} kcalです")

    # 料理名のテキストボックスが空の時に警告を出す
    if not dish_name:
        st.warning("料理名を入力してください！")

    # 正しいファイル形式の画像をアップロードして場合は消える警告
    if uploaded_file is None:
        st.warning("写真なし、または対応外の形式のファイルがアップロードされています。その場合は料理名のみで推定します。")










if __name__ == "__main__":
    main()