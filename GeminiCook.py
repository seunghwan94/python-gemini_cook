import streamlit as st
from streamlit_tags import st_tags
import configparser
import os
import google.generativeai as genai
import re
from bs4 import BeautifulSoup
import json
import requests

def txtCreateRead(txt_file):
    # 파일 생성
    try:
        with open(txt_file, "r", encoding="UTF-8") as f:
            pass
    except FileNotFoundError:
        # 파일이 존재하지 않는 경우
        with open(txt_file, "w", encoding="UTF-8") as f:
            f.write("")

    # 파일 읽기
    set_text = []
    if os.path.exists(txt_file):
        with open(txt_file, "r", encoding="UTF-8") as f:
            for line in f:
                set_text.append(line.strip())

    # JSON 형식의 문자열을 딕셔너리로 변환
    setting_list = {}
    if set_text:
        setting_list = json.loads(set_text[0])

    return setting_list

def saveTxt(key_value,txt_file, is_set=False):
    # 기존 데이터 불러오기
    if is_set:
        try:
            with open(f"{txt_file}", "r", encoding="UTF-8") as f:
                existing_data = json.load(f)
            # 새로운 키-값 쌍 추가
            existing_data.update(key_value)
        except:
            # 공백일 경우
            existing_data = ""
    else:
        existing_data = key_value

    # 수정된 데이터를 파일에 저장
    with open(f"{txt_file}", "w", encoding="UTF-8") as f:
        json.dump(existing_data, f)

# 요리 목록 파씽
def parse_list(html):
    # 정규 표현식을 사용하여 각 요리 제목과 설명을 추출합니다.
    soup = BeautifulSoup(html, 'html.parser')

    # 각 요리 제목과 설명을 추출
    recipes = []

    # 비슷한 요리와 새로운 요리에 대해 각각 처리
    for category in soup.find_all('ul'):
        for item in category.find_all('li'):
            title = item.find('b').text.strip()
            description = item.contents[1].strip().replace(':', '')
            recipes.append((title, description))

    return recipes

# 제미나이 출력
def Gemini( api_key, gemini_type, prompt ):

    genai.configure(api_key=api_key)
    # 모델 로드
    model = genai.GenerativeModel(gemini_type)
    # 요청
    response = model.generate_content(f' {prompt} 한국어로 알려줘')

    return response.text

# 프롬프트 작성
def prompt(food_type, ingredients_tags,  favorite_food_tags, remove_list):
    # step2 더보기
    if remove_list != '':
        remove_list_temp = ', '.join(list(remove_list.keys()))
        remove_list = f'({remove_list_temp} 목록에서 제외) 새로운'
    # 좋아하는 음식
    favorite_food_tags_str = ', '.join(favorite_food_tags)
    favorite_food_prompt = f'{favorite_food_tags_str} 비슷한 '
    # 재료
    ingredients_tags_str = ', '.join(ingredients_tags)
    # 결과
    favorite_ingredients_prompt = ingredients_tags_str + f' 재료들이 있는데 이걸로 만들수 있는 {favorite_food_prompt} {food_type}요리 5개 리스트{remove_list} 목록이랑 설명만 출력해서 html 코드로 알려주는데 요리 제목은 b태그로 알려줘'

    return favorite_ingredients_prompt, favorite_food_prompt

def step3(type, title, favorite_food_tags ):

    prompt =f'{favorite_food_tags} 비슷한 느낌이 나는 {title}를 만들고싶어' \
            f'제목은 {title}로 해주고, 15살 및 {favorite_food_tags} 이라는 단어는 쓰지말아줘' \
            f'최대한 구체적으로 알려줘서 15살 아이도 같은 맛을 낼수 있도록 이해하기 쉽게 알려주고, ' \
            f'계량은 종이컵기준으로 잡아주고, markdown으로 알려줘 ' \

    return prompt
##################################################################################################################################

txt_file = 'setting.txt'
setting_list = txtCreateRead(txt_file)

# 파일을 UTF-8 인코딩으 읽기
config = configparser.ConfigParser()
with open(os.getcwd() + '/config.ini', 'r', encoding='utf-8') as f:
    config.read_file(f)

ingredients_str = config['etc']['ingredients']
ingredients = ingredients_str.strip('[]').split(',')

favorite_food_str = config['etc']['favorite_food']
favorite_food = favorite_food_str.strip('[]').split(',')

# 세션 상태를 초기화합니다.
if 'active_tab' not in st.session_state:
    st.session_state.active_tab = 'step1'
if 'cook_list' not in st.session_state:
    st.session_state.cook_list = {}
if 'select_food' not in st.session_state:
    st.session_state.select_food = {}
    st.session_state.select_img = {}

# radio 가로 정렬
st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)
# Streamlit 페이지 제목 설정
st.title("GeminiCook")

# 현재 active_tab에 따라 탭 내용 표시
if st.session_state.active_tab == 'step1':
    # 초기화
    st.session_state.cook_list = {}
    # session state 값 확인
    if 'Gemini_api_key' not in st.session_state:
        st.session_state.Gemini_api_key = setting_list.get("Gemini_api_key", "")
        if 'Gemini_api_key' not in st.session_state:
            st.session_state.Gemini_api_key = None

    Gemini_url = 'https://platform.openai.com/account/api-keys'
    st.session_state.Gemini_api_key = st.text_input('Gemini API KEY [Gemini API 사이트 바로가기](%s)' % Gemini_url, value=setting_list.get("Gemini_api_key", "")).strip()

    #
    Gemini_type_mapping = ['gemini-1.5-flash', 'gemini-1.5-pro']
    Gemini_type_default = Gemini_type_mapping.index(setting_list.get("Gemini_type", 'gemini-1.5-flash'))
    st.session_state.Gemini_type = st.radio(
        "Gemini 버전 선택",
        options=Gemini_type_mapping,
        index=Gemini_type_default
    )

    food_type_mapping = {'양식': '서양식', '중식': '중국식', '일식': '일본식', '한식': '한국식',}
    food_type_default = list(food_type_mapping.values()).index(setting_list.get("food_type", '서양식'))
    st.session_state.food_type = food_type_mapping[st.radio(
        "원하는 음식 종류 선택",
        options=food_type_mapping,
        index=food_type_default
    )]

    st.session_state.favorite_food_tags = st_tags(
        label='가장 좋아하는 요리를 작성해주세요',
        text='추가하려면 Enter 키를 누릅니다',
        value=['김치찌개', '라자냐', '알리오올리오'],
        suggestions=favorite_food,
        maxtags=5,
        key='1'
    )

    st.session_state.ingredients_tags = st_tags(
        label='요리에 사용하고싶은 재료를 넣어주세요',
        text='추가하려면 Enter 키를 누릅니다',
        value=['고추장', '된장', '삼겹살'],
        suggestions=ingredients,
        maxtags=100,
        key='2'
    )

    st.subheader('이미지를 원하시는 경우 (선택) [Gemini API 사용방법](%s)'%'https://developers.google.com/custom-search/v1/introduction?apix=true&hl=ko')
    st.write()
    st.session_state.Google_SEARCH_ENGINE_ID = st.text_input('Google SEARCH ENGINE ID [Google SEARCH ENGINE ID 사이트 바로가기](%s)' % 'https://programmablesearchengine.google.com/controlpanel/all',
                                                             value=setting_list.get("Google_SEARCH_ENGINE_ID",
                                                                                    "")).strip()
    st.session_state.Google_API_KEY = st.text_input('Google API KEY [Google_API_KEY 사이트 바로가기](%s)' % 'https://console.cloud.google.com/apis/library/customsearch.googleapis.com?project=geminiimg',
                                                    value=setting_list.get("Google_API_KEY", "")).strip()

    col1, col2 = st.columns([9, 1])
    btn_save = col2.button('다음')

    if btn_save:
        # 입력 받은 정보를 딕셔너리로 저장
        blog_info = {
            "Gemini_api_key": st.session_state.Gemini_api_key,
            "Gemini_type": st.session_state.Gemini_type,
            "food_type": st.session_state.food_type,
            "Google_API_KEY" : st.session_state.Google_API_KEY,
            "Google_SEARCH_ENGINE_ID" : st.session_state.Google_SEARCH_ENGINE_ID
        }
        saveTxt(blog_info, txt_file)


        favorite_ingredients_prompt, st.session_state.favorite_food_prompt = prompt(st.session_state.food_type, st.session_state.ingredients_tags, st.session_state.favorite_food_tags, '')

        # 요리 목록 뽑기
        for i in range(3):
            cook_list_temp = Gemini(st.session_state.Gemini_api_key, st.session_state.Gemini_type, favorite_ingredients_prompt)
            try:
                # 요리 목록 파싱
                cook_list = parse_list(cook_list_temp)

                for title, description in cook_list:
                    st.session_state.cook_list[title] = description

                st.session_state.active_tab = 'step2'
                break
            except Exception as e:
                continue

        if st.session_state.active_tab == 'step2':
            st.experimental_rerun()

elif st.session_state.active_tab == 'step2':

    if st.session_state.cook_list:
        st.header(f"{st.session_state.food_type} 요리 목록")

        for title, description in st.session_state.cook_list.items():

            try:
                query = title  # 검색할 쿼리
                start_page = "1"  # 몇 페이지를 검색할 것인지. 한 페이지 당 10개의 게시물을 받아들일 수 있습니다.

                url = f"https://www.googleapis.com/customsearch/v1?key={st.session_state.Google_API_KEY}&cx={st.session_state.Google_SEARCH_ENGINE_ID}&q={query}&start={start_page}"

                response = requests.get(url).json()
                col1, col2 = st.columns([1,2])

                img = response['items'][1]['pagemap']['cse_thumbnail'][0]['src']
            except:
                img = 'test.png'

            col1.image(img, width=200)
            col2.subheader(title)
            col2.write(description)

            if col2.button(f"{title} 레시피 보기"):
                st.session_state.select_food = title
                st.session_state.select_img[title] = img
                st.session_state.active_tab = 'step3'
                st.experimental_rerun()

        col_btn1, col_btn2 = st.columns([2,2])
        btn_back = col_btn1.button('이전 단계로')

        btn_more = col_btn2.button('+ 더 보기')

        if btn_back:
            st.session_state.active_tab = 'step1'
            st.session_state.cook_list = {}
            st.experimental_rerun()
        elif btn_more:
            favorite_ingredients_prompt, st.session_state.favorite_food_prompt = prompt(st.session_state.food_type,
                                                                                       st.session_state.ingredients_tags,
                                                                                       st.session_state.favorite_food_tags,
                                                                                       st.session_state.cook_list)
            # 요리 목록 뽑기
            cook_list_temp = Gemini(st.session_state.Gemini_api_key, st.session_state.Gemini_type,
                                    favorite_ingredients_prompt)
            # 요리 목록 파싱
            cook_list = parse_list(cook_list_temp)
            for title, description in cook_list:
                st.session_state.cook_list[title] = description
            st.experimental_rerun()
    else:
        st.error('오류가 발생하여 새로고침 바랍니다.')

elif st.session_state.select_food and st.session_state.active_tab == 'step3':
    # 데이터 초기화
    table_ingredient = []
    table_recipe = []

    # 데이터 가져오기
    recipe_prompt = step3(st.session_state.Gemini_type, st.session_state.select_food, st.session_state.favorite_food_prompt)
    recipe_temp = Gemini(st.session_state.Gemini_api_key, st.session_state.Gemini_type, recipe_prompt)
    st.image(st.session_state.select_img[st.session_state.select_food], width=300)
    st.markdown(recipe_temp)

    col1, col2 = st.columns([3, 1])

    btn_back = col1.button('이전 단계로')
    btn_reset = col2.button('새로운 레시피 뽑기')

    if btn_back:
        st.session_state.active_tab = 'step2'
        st.session_state.select_food = {}
        st.experimental_rerun()
    elif btn_reset:
        st.experimental_rerun()

else:
    st.write('오류가 발생하여 새로고침 부탁드립니다.')
