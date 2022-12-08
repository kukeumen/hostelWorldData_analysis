from selenium import webdriver
import pandas as pd
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
from matplotlib import rc
import platform
if platform.system() == 'Darwin': #맥
    rc('font', family='AppleGothic')
elif platform.system() == 'Windows': #윈도우 한글 깨지지 않게 설정
    rc('font', family='Malgun Gothic') 
    
def bs4_element_ToString(str_list):
    #bs4_element type의 데이터를 String type으로 변환하는 함수
    result = ""
    for s in str_list:
        result += str(s) + " "
    return result.strip()

#월별 숙소 데이터 수집
##------ 수집 연도, 월에 맞게 수정 -----##
year = "2023"
month = "01"
day = "1"
end_condition = ("%s-%s-%s"%(year,month,day)!="2023-01-31")
save_file_name = "1월_hostelsWorld_data.csv"
##------------------------------------##


data_columns = ['hostel_name', 'checkin_date', 'checkout_date', 'city', 'distance', 'room_type','room_charge', 'num_reviews', 'review_total_score']
hostelsWorld_df = pd.DataFrame(columns=data_columns)
#드라이버 실행
while end_condition !="2023-01-31":
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
    city = 'Tokyo'
    checkin_date = "%s-%s-%s"%(year,month,day) #입실 날짜
    checkout_date = "%s-%s-%s"%(year,month,str(int(day)+1)) #퇴실 날짜
    if int(day) >=0 and int(day)<=9:
        checkin_date = "%s-%s-%s"%(year,month,"0"+day) #입실 날짜
        checkout_date = "%s-%s-%s"%(year,month,"0"+str(int(day)+1)) #퇴실 날짜
    

    print("%s ~ %s Start!"%(checkin_date, checkout_date))
    hostel_url = "https://www.hostelworld.com/s?q=Tokyo,Japan&country=Japan&city=Tokyo&type=city&id=452&from=%10s&to=%10s&guests=2&page=1&sort=rating"%(checkin_date, checkout_date)
    driver.get(hostel_url)
    body = driver.find_element(By.TAG_NAME, 'body')
    
    import time
    for i in range(10): #10번 정도 스크롤 다운하면 전부 볼 수 있어서 10으로 설정.
        body.send_keys(Keys.PAGE_DOWN)
        time.sleep(1) #적당한 시간으로 페이지 다운
    
    hostels_html = driver.page_source #페이지소스 가져와서 html에 저장
    driver.close()
    
    # 숙박 인원 2명 기준 데이터 수집 
    ##### 숙소 데이터 #####
    # 이미 선언된 변수
    # checkin_date = [] #입실 날짜
    # checkout_date = [] #퇴실 날짜
    # city = [] #숙소가 위치한 도시
    hostel_name = [] #숙소(호스텔) 이름
    distance = [] #도시중심부에서 숙소까지의 거리 (단위 km)
    room_type = [] #Private or Dorms
    room_charge = [] #숙소 최저 가격
    
    ##### 리뷰 데이터 #####
    num_reviews = [] #해당 숙소에 대한 리뷰 개수
    review_total_score = [] #해당 숙소에 대한 리뷰 평점 (0~10)
    
    page_parser = BeautifulSoup(hostels_html, 'html.parser')
    property_card_raw = page_parser.find_all('div','property-card') #호텔 하나하나의 정보를 리스트로 받아옴.
    
    for i in range(len(property_card_raw)):
        temp_property = str(property_card_raw[i]) # 현재 property card 의 태그 정보를 string 으로 변환
        temp_parser = BeautifulSoup(temp_property, 'html.parser') #현재 property card 의 태그 정보를 html parser 로 선언
        featured_list = temp_parser.find('div', 'score orange small')
        if featured_list is not None:
            continue
    ##### 리뷰 데이터 #####
        try:
            review_score = temp_parser.find('div', 'keyword').get_text().strip()
            if review_score=="No Rating":
                review_total_score = "NO"
            else:
                review_total_score = temp_parser.find('div', 'score orange big').get_text().strip()
            num_reviews = temp_parser.find('div', 'reviews').get_text().strip()
            
            ##### 숙소 데이터 #####
            hostel_name = temp_parser.find('h2', 'title title-6').get_text().strip() #숙소 이름
            distance = temp_parser.find('span', 'description').get_text().strip() #도시중심부부터 숙소까지의 거리
            # 1)private, dorm 둘 다 있음, 2) private만, 3) dorm만 4) 둘 다 없음
            room_elements = temp_parser.find('div', 'prices-col')
            room_elements = bs4_element_ToString(room_elements)
            room_parser = BeautifulSoup(room_elements, 'html.parser')
            room_type_and_charges = room_parser.find_all('div', 'price-col')
            room_type_and_charges_list = []
            for i in room_type_and_charges:
                t = i.get_text().strip()
                room_type_and_charges_list.append(t)
            
            room_type = []
            room_charge = []
            for i in room_type_and_charges_list:
                if i.find('Privates')>=0: #있다면
                    temp_room_type = "PRIVATE"
                elif i.find('Dorms')>=0:
                    temp_room_type = "DORMS"
                charge_idx = i.find("\n")
                temp_room_charge = i[charge_idx:]
                room_type.append(temp_room_type)
                room_charge.append(temp_room_charge.strip())
            
            for temp_type, temp_charge in zip(room_type, room_charge): 
                temp_data = {'hostel_name':[hostel_name], 'checkin_date': [checkin_date], 
                             'checkout_date':[checkout_date], 'city': [city], 
                             'distance':[distance], 'room_type':[temp_type],
                             'room_charge':[temp_charge], 'num_reviews':[num_reviews], 
                             'review_total_score':[review_total_score]}
                temp_df = pd.DataFrame(data=temp_data)
                hostelsWorld_df = pd.concat([hostelsWorld_df, temp_df])
        except:
                continue
    day = str(int(day)+1)
    print("Today is done!\n")
    end_condition=checkout_date

hostelsWorld_df.to_csv("hostelsWorld_data.csv", index=False, encoding='utf-8')
print("Crawling done!")
