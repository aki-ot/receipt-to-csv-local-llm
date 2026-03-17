import os
import glob
import json
import pandas as pd
import re
import time
from datetime import datetime
import shutil

import ai_classifier

INPUT_DIR = "data/input"
OUTPUT_DIR = "data/output"
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png"}
PROCESSED_DIR = "data/processed"

os.makedirs(PROCESSED_DIR, exist_ok=True)

def get_input_files(dir_path):
    """入力フォルダから画像ファイルのリストを取得する"""
    files = []
    for ext in ALLOWED_EXTENSIONS:
        # 大文字小文字の両方に対応
        files.extend(glob.glob(os.path.join(dir_path, f"*{ext}")))
        files.extend(glob.glob(os.path.join(dir_path, f"*{ext.upper()}")))
    return list(set(files))

def save_result(df, name):
    # 1. タイムスタンプと元ファイル名を取得
    date_str = datetime.now().strftime('%Y-%m-%d')
    
    # 2. 保存先ディレクトリ作成 (data/output/2026-02-19/ みたいな形)
    output_dir = os.path.join("data", "output", date_str)
    os.makedirs(output_dir, exist_ok=True)
    
    # 3. 保存
    df.to_csv(name, index=False, encoding='utf-8-sig')
    print(f"Saved: {name}")

def main():
    try:
        # 1. ファイル一覧の取得
        image_files = get_input_files(INPUT_DIR)
        if not image_files:
            print("処理対象の画像が見つかりませんでした。")
            return
        
        all_receipt_data = []
        for image_path in image_files:

            # --- 計測開始 ---
            start_time = time.time()
            print(f"解析開始時刻: {time.strftime('%H:%M:%S')}")
            
            print(f"AI解析中: {image_path}...")
            raw_json_str = ai_classifier.analyze_receipt_with_vl(image_path)
            
            # --- 計測終了 ---
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            # JSONのパース
            json_clean = re.sub(r'```json|```|\n', '', raw_json_str).strip()
            

            data = json.loads(json_clean)
            
            # 商品リストをDataFrame化
            df = pd.DataFrame(data['Items'])
            
            # 店名と日付を全ての行に付与
            df['Store'] = data.get('Store', '不明')
            df['Date'] = data.get('Date', '不明')
            
            # 列の順番を整理（日付, 店名, 商品名, 価格）
            df = df[['Date', 'Store', 'Item', 'Price', 'Category']]
            
            print("\n--- 抽出結果 ---")
            print(df)
            print(f"\n処理時間: {elapsed_time:.2f} 秒")
            print(f"終了時刻: {time.strftime('%H:%M:%S')}")

            all_receipt_data.append(df)

            # 移動先のパスを作成
            dest_path = os.path.join(PROCESSED_DIR, os.path.basename(image_path))
            
            # ファイルを移動
            shutil.move(image_path, dest_path)
            print(f"Moved to processed: {os.path.basename(image_path)}")

        # 保存
        if all_receipt_data:
            final_df = pd.concat(all_receipt_data, ignore_index=True)

            date_str = datetime.now().strftime('%Y-%m-%d')
            save_dir = os.path.join(OUTPUT_DIR, date_str)
            os.makedirs(save_dir, exist_ok=True)
            
            timestamp = datetime.now().strftime('%H%M%S')
            output_path = os.path.join(save_dir, f"combined_receipts_{timestamp}.csv")
            
            save_result(final_df, output_path)

    except Exception as e:
        print(f"解析エラー: {e}")
        print(f"AIの応答: {raw_json_str}")

if __name__ == "__main__":
    main()
