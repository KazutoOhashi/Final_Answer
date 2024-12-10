from time import sleep
from collections import defaultdict
import re
import pandas as pd
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import WebDriverException, NoSuchElementException
from selenium.webdriver.chrome.options import Options

# ユーザエージェントを指定
user_agent = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36'

# ウェブドライバーの設定
options = Options()
options.add_argument(f'user-agent = {user_agent}')
options.add_argument('--headless')
driver = webdriver.Chrome(options = options)

elem_dict = defaultdict(list) # データを格納する辞書
n_shops = 0 # 店舗数カウンタ

base_url = 'https://r.gnavi.co.jp/area/kyoto/rs/' # ベースURL
driver.get(base_url)
sleep(1)

try:
    while n_shops < 50: # 店舗数が50になるまで繰り返す
        # 店舗情報一覧を取得
        shop_windows = driver.find_elements(By.CLASS_NAME, 'style_title___HrjW')
        shop_links = [shop_window.find_element(By.TAG_NAME, 'a').get_attribute('href') for shop_window in shop_windows]
        # 店舗情報を順に処理
        for shop_link in shop_links:
            driver.get(shop_link)
            sleep(3)

            shop_info = driver.find_element(By.ID, 'info-table')

            name = shop_info.find_element(By.ID, 'info-name').text # 店舗名を取得
            if name in elem_dict['店舗名']:
                continue # 店舗に被りがある場合、スキップして処理を継続

            phone = shop_info.find_element(By.CLASS_NAME, 'number').text # 電話番号を取得

            # 住所を取得し、都道府県、市区町村、番地に分割
            region = shop_info.find_element(By.CLASS_NAME, 'region').text
            prefecture = re.search(r'\S+府', region).group()
            match = re.search(r'\d.*', region) # 住所に数字が含まれるかを判定
            if match:
                street = "'" + match.group() # エクセル上で文字列として扱うため、先頭に'をつけている
            else:
                street = None
            city = region.replace(prefecture, '').replace(street.strip("'") if street else '', '')

            # 建物名の記載がある場合、建物名を取得
            try:
                building = shop_info.find_element(By.CLASS_NAME, 'locality').text
            except NoSuchElementException:
                building = None

            # 公式ページの掲載がある場合、公式ページのURLを取得
            try:
                official_page_link = driver.find_element(By.CLASS_NAME, 'sv-of').get_attribute('href')
            except NoSuchElementException:
                try:
                    official_page_link = shop_info.find_element(By.CLASS_NAME, 'url').get_attribute('href')
                except NoSuchElementException:
                    official_page_link = None
            if official_page_link:
                try:
                    driver.get(official_page_link)
                    sleep(3)
                    url = driver.current_url
                except: # 公式ページへのアクセスに失敗した場合、URLを空にして処理を継続
                    print(f'Error has occurred in accessing the officail page. URL: {official_page_link}')
                    url = None
            # 公式ページのURLについてSSL証明書の有無を取得
            if url:
                try:
                    ssl = requests.get(url, verify = True)
                    ssl = True
                except requests.exceptions.SSLError:
                    ssl = False
            else:
                ssl = None

            # 取得したデータを辞書に追加
            elem_dict['店舗名'].append(name)
            elem_dict['電話番号'].append(phone)
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

        # 次ページへ遷移
        driver.get(base_url)
        next_button = driver.find_element(By.CLASS_NAME, 'style_pages__Y9bbR').find_elements(By.TAG_NAME, 'li')[-2]
        if next_button:
            next_button.click()
            print('Visiting a next page.')
            sleep(1)
        else:
            print('Next page is not found.')
            break # 次ページが見つからない場合、ループを抜ける
    print(f'Data aquisition has been completed.')

except WebDriverException as e:
    print(f'WebDriver error has occurred. {e}')
    exit(1) # ウェブドライバーエラーが発生した場合、処理を中断
except Exception as e:
    print(f'Unexpected error has occurred. {e}')
    exit(1) # その他のエラーが発生した場合、処理を中断
finally:
    driver.quit()

# データフレームの作成、保存
df = pd.DataFrame(elem_dict)
df.to_csv('1-2.csv', index = False, encoding = 'utf-8-sig')
print('CSV file has been saved successfully.')