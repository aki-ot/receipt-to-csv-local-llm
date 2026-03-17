import ollama
import base64
from io import BytesIO
from PIL import Image

def image_to_base64(image_path):
    img = Image.open(image_path)
    img.thumbnail((1000, 1000))
    buffered = BytesIO()
    img.save(buffered, format="JPEG")
    return base64.b64encode(buffered.getvalue()).decode('utf-8')

def analyze_receipt_with_vl(image_path):
    img_base64 = image_to_base64(image_path)
    
    # 店名と日付も抽出対象に追加
    prompt = """
        このレシート画像から「店名」「日付」「各商品の名前、価格、カテゴリ」を抽出して、以下のJSON形式のみで出力してください。
                
        【厳守事項】
        1. 商品名の加工: 
           - 読み取った商品名は、必ず「意味の通る正しい全角日本語」に変換してください。
           - 特にヌイー・ハイーはスの可能性が高いです。
        2. カテゴリ判定:
            - 以下のリストから「一言一句変えずに」1つ選んでください。
            - リスト：[衣服, 美容/健康, 医療品, 雑貨, 食費, 日用品, 玩具, その他]
        3. 不要な行の除外:
           - 「合計」「お預り」「お釣り」等は「商品（Items）」ではないため、絶対に含めないでください。
        4. 出力形式:
           - 解説や挨拶は一切禁止。JSONデータのみを出力してください。        

        {
          "Store": "店名",
          "Date": "YYYY-MM-DD",
          "Items": [
            {"Item": "商品名1", "Price": 100, "Category": "<カテゴリ>"},
            {"Item": "商品名2", "Price": 200, "Category": "<カテゴリ>"}
          ]
        }
        """

    response = ollama.generate(
        model='qwen2.5vl:3b',
        prompt=prompt,
        images=[img_base64],
        stream=False,
        options={'temperature': 0}
    )
    
    return response['response']