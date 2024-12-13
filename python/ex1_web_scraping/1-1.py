from time import sleep
from urllib.parse import urljoin
from collections import defaultdict
import re
import pandas as pd
import requests
from bs4 import BeautifulSoup

# ユーザエージェントを指定
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'}

elem_dict = defaultdict(list) # データを格納する辞書
n_shops = 0 # 店舗数カウンタ

base_url = 'https://r.gnavi.co.jp/area/kyoto/rs/' # ベースURL

try:
    while n_shops < 50: # 店舗数が50になるまで繰り返す
        res = requests.get(base_url, headers = headers)
        res.raise_for_status()
        soup = BeautifulSoup(res.text, 'html.parser')
        sleep(1)
        # 店舗情報一覧を取得
        shop_windows = soup.find_all(class_ = 'style_title___HrjW')
        shop_links = [shop_window.find('a').get('href') for shop_window in shop_windows]
        # 店舗情報を順に処理
        for shop_link in shop_links:
            shop_res = requests.get(shop_link)
            res.raise_for_status()
            shop_soup = BeautifulSoup(shop_res.text, 'html.parser')
            sleep(3)

            # requestsでHTML要素を抽出すると日本語が文字化けしたため、文字列はlatin-1でエンコードした後UTF-8でデコードし直している
            shop_info = shop_soup.find(id = 'info-table')

            name = shop_info.find(id = 'info-name').text.encode('latin1').decode('utf-8', errors = 'ignore') # 店舗名を取得
            if name in elem_dict['店舗名']:
                continue # 店舗に被りがある場合、スキップして処理を継続

            phone = shop_info.find(class_ = 'number').text # 電話番号を取得

            # 住所を取得し、都道府県、市区町村、番地に分割
            region = shop_info.find(class_ = 'region').text.encode('latin1').decode('utf-8')
            prefecture = re.search(r'\S+府', region).group()
            match = re.search(r'\d.*', region) # 住所に数字が含まれるかを判定
            if match:
                street = "'" + match.group() # エクセル上で文字列として扱うため、先頭に'をつけている
            else:
                street = None
            city = region.replace(prefecture, '').replace(street.strip("'") if street else '', '')

            # 建物名の記載がある場合、建物名を取得
            try:
                building = shop_info.find(class_ = 'locality').text.encode('latin1').decode('utf-8')
            except:
                building = None

            # requestsではURLが取得不可のため空にしておく
            url = None
            ssl = None

            # 取得したデータを辞書に追加
            elem_dict['店舗名'].append(name)
            elem_dict['電話番号'].append(phone)
            elem_dict['メールアドレス'].append(None)
            elem_dict['都道府県'].append(prefecture)
            elem_dict['市区町村'].append(city)
            elem_dict['番地'].append(street)
            elem_dict['建物名'].append(building)
            elem_dict['URL'].append(url)
            elem_dict['SSL'].append(ssl)

            n_shops += 1 # 店舗数を更新
            print(f'Data of {name} has been aquired.\nn_shops: {n_shops}')
            if n_shops >= 50:
                break

        # 次ページへのリンクを取得
        next_page_link = soup.find(class_ = 'style_pages__Y9bbR').find_all('li')[-2].find('a').get('href')
        if next_page_link:
            next_page_link = urljoin('https://r.gnavi.co.jp/', next_page_link)
            base_url = next_page_link
            print('Visiting a next page.')
        else:
            print('A next page is not found.')
            break # 次ページが見つからない場合、ループを抜ける
    print(f'Data aquisition has been completed.')

except requests.exceptions.HTTPError as e:
    print(f'HTTP error has occurred. {e}')
    exit(1) # HTTPエラーが発生した場合、処理を中断
except Exception as e:
    print(f'Unexpected error has occurred. {e}')
    exit(1) # その他のエラーが発生した場合、処理を中断

# データフレームの作成、保存
df = pd.DataFrame(elem_dict)
df.to_csv('1-1.csv', index = False, encoding = 'utf-8-sig')
print('CSV file has been saved successfully.')