import streamlit as st
import folium
import geopandas as gpd
from folium.features import DivIcon
from streamlit_folium import st_folium
import json
import pandas as pd
from openai import OpenAI
import os

# --- 페이지 설정 ---
st.set_page_config(
    page_title="산업단지 화재 위험도 맵",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -- insert your OpenAI API key here or set it as an environment variable ---
api_key = os.getenv("OPENAI_API_KEY")

if not api_key:
    st.error("Not found OpenAI API Key. Please set your API key in the environment variable 'OPENAI_API_KEY'.")
    st.stop()

client = OpenAI(api_key=api_key)

# ---- 산업단지별 파일 매핑 ----
industrial_areas = {
    "발안일반산업단지": {
        "geojson": "data/dashboard/발안산업단지_최종스코어링_결과.geojson",
        "csv": "data/dashboard/발안산업단지.csv",
        "buffer_geojson": "data/dashboard/발안_젤위험_버퍼600.geojson"
    },
    "향남제약일반산업단지": {
        "geojson": "data/dashboard/향남산업단지_최종스코어링_결과.geojson",
        "csv": "data/dashboard/향남제약산업단지111.csv",
        "buffer_geojson": "data/dashboard/향남_젤위험_버퍼600.geojson"
    },
    "동탄도시첨단산업단지": {
        "geojson": "data/dashboard/동탄도시첨단산업단지_최종스코어링_결과.geojson",
        "csv": "data/dashboard/동탄도시첨단산업단지111.csv",
        "buffer_geojson": "data/dashboard/동도첨_젤위험_버퍼600.geojson"
    }
}

# ---- 산업단지 화재위험도 분석 prompt scenario ----
@st.cache_data(show_spinner=False)
def get_area_summary_cached(area_name, csv_path):
    try:
        df = pd.read_csv(csv_path, encoding="utf-8")
        sample = df.to_string(index=False)
        prompt = f"""
당신은 산업단지의 위험도를 분석하는 데이터 분석가입니다.

아래는 {area_name}의 화재 위험요인 데이터입니다. 이는 각 구역별로 id가 있으며, 화재 위험 요인 feature별 화재 위험 수준 값이 있습니다.
{sample}

위 데이터의 feature는 화재 위험도를 평가하는 요소이며, 값은 feature의 개수가 아닌 화재 위험 수준입니다. 이는 숫자가 높을수록 위험하며, 낮을 수록 안전합니다.

우리에게는 세 가지 예산 별 대책이 존재합니다.
저예산은 기본 교육, 소방시설 점검, 현장 컨설팅이 기본적인 방안이며 우리가 제안하고자 하는 방안은 AI CCTV 설치, 화재 알림 경보 시스템이고 적용 예시로는 소규모 공장, 취약사업장 중심에 적용하는 것이 있습니다.
중간 예산으로는 위험요인 식별, 소방 훈련, 용수시설 확충, 예방강화지구 지정이 기본적인 방안이며 우리가 제안하고자 하는 방안은 화재 예측 모델 도입, AI 기반 실시간 화재 감지가 있고 적용 예시로는 표준 산업단지, 업종별 맞춤 관리가 있습니다.
고예산으로는 첨단예측&대응, 대규모 인프라, 통합관제, 특수시설 구축이 기본적인 방안이며 우리가 제안하고자 하는 방안은 AI 통합 화재 모니터링 센터 구축, 스마트 화재대응 플랫폼이 있고 적용 예시로는 국가산단, 대형화재 및 복합재난 대응이 있습니다.

따라서, 우리는 해당 산업단지가 종합적으로 어느정도 화재 위험도를 가지는지 판별하여 해당 산업단지에 예산 투입 수준을 판단하고 대응 방안을 제안합니다.
1. {area_name}의 화재 위험요인과 방재 취약 요소를 판단하고 제시합니다.
2. 어떤 예산 도입 (저/중/고)이 필요한지 판별 후 위 대응책과 매치하여 AI/스마트 대응방안 및 적용 예시를 제안합니다. 
각 결과는 전문성이 있는 글이어야 하며, 판단 이유가 타당해야 합니다. 각 결과는 1~2줄로 요약해주세요.

예시) 발안산업단지를 분석한다. -> 우리 데이터를 확인하여 분석 요약 및 위험 요인과 방재 취약 요소 파악 후, 어떤 수준의 대응이 필요한지 설명 및 대응 방안 제시.
🔶 발안산업단지
분석 요약: 위험물 취급 시설, 고밀도 건물 등이 다수 존재하며, 소방차 접근성과 소방서 거리 등 방재 여건이 매우 열악함.

위험 요인: 위험물회사 밀집, 건물밀도 높음

방재 취약 요소: 소방차 접근 불가, 소방서 원거리

적용 대응책:
👉 중간 예산 수준 대응 필요

주요 대책: 위험요인 선별, 소방훈련 강화, 용수시설 추가

AI 방안: 화재 예측 모델 및 실시간 경고 시스템

적용 예시: 표준 산업단지 중 위험구역 우선 조치
"""
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=600,
            temperature=0.7
        )
        summary = response.choices[0].message.content.strip()
        return summary
    except Exception as e:
        return f"요약 생성 오류: {e}"

with st.sidebar:
    st.header("📂 산업단지 선택")
    selected_area = st.selectbox("산업단지", list(industrial_areas.keys()))
    use_color = st.checkbox("화재 위험도 5클래스 색상 및 텍스트 표시", value=True)
    show_buffer = st.checkbox("버퍼 분석 레이어 표시", value=False)

    legend_html = '''
<div style="background-color: #222; color: #fff; border: 2px solid #444; border-radius: 8px; padding: 14px 14px 10px 14px; margin-bottom: 18px; margin-top:10px; font-size: 15px; font-weight: 500; letter-spacing: 0.5px;">
<b style="color:#fff;">화재 위험도 색상 범례</b><br>
<div style='background:#ffffff; color:#111; width: 20px; height: 20px; display: inline-block; border: 1px solid #999; margin-right: 8px; vertical-align:middle;'></div> <span style="color:#fff;">매우 낮음</span><br>
<div style='background:#ffcccc; color:#111; width: 20px; height: 20px; display: inline-block; border: 1px solid #999; margin-right: 8px; vertical-align:middle;'></div> <span style="color:#fff;">낮음</span><br>
<div style='background:#ff9999; color:#111; width: 20px; height: 20px; display: inline-block; border: 1px solid #999; margin-right: 8px; vertical-align:middle;'></div> <span style="color:#fff;">보통</span><br>
<div style='background:#ff6666; color:#111; width: 20px; height: 20px; display: inline-block; border: 1px solid #999; margin-right: 8px; vertical-align:middle;'></div> <span style="color:#fff;">높음</span><br>
<div style='background:#ff0000; color:#fff; width: 20px; height: 20px; display: inline-block; border: 1px solid #999; margin-right: 8px; vertical-align:middle;'></div> <span style="color:#fff;">매우 높음</span>
</div>
'''
    st.markdown(legend_html, unsafe_allow_html=True)
    
    st.markdown("---")
    with st.spinner(f"{selected_area} AI 요약 생성 중..."):
        summary = get_area_summary_cached(selected_area, industrial_areas[selected_area]["csv"])
    summary_html=summary.replace("\n", "<br>")
    st.markdown(
        f"""
        <div style="background-color:#222; color:#fff; border-radius:10px; padding:16px; margin-top:10px; margin-bottom:10px;">
        <b>📋 {selected_area} 화재 위험도 분석 및 대응 방안</b><br>
        {summary_html}
        </div>
        """,
        unsafe_allow_html=True
    )
    st.markdown("---")
    st.markdown("#### 🖱️ 지도 조작 안내")
    st.markdown("""
- 마우스 휠로 확대/축소  
- 드래그로 이동  
- 범례와 수치는 위험도 등급입니다.
""")
    
geojson_path = industrial_areas[selected_area]["geojson"]
csv_path = industrial_areas[selected_area]["csv"]
buffer_geojson_path = industrial_areas[selected_area]["buffer_geojson"]

# ---- Process GeoJSON ----
with open(geojson_path, encoding="utf-8") as f:
    gj = json.load(f)
    property_keys = list(gj["features"][0]["properties"].keys())
    last_property_col = property_keys[-1]

# ---- Functions ----
def get_color_balan(value):
    try: value = float(value)
    except: return "#cccccc"
    if -0.3 < value <= -0.15: return "#ffffff"
    elif -0.15 < value <= 0.25: return "#ffcccc"
    elif 0.25 < value <= 1.2: return "#ff9999"
    elif 1.2 < value <= 1.95: return "#ff6666"
    elif 1.95 < value <= 2.35: return "#ff0000"
    else: return "#cccccc"

def get_color_hyangnam(value):
    try: value = float(value)
    except: return "#cccccc"
    if 0.4 < value <= 0.4: return "#ffffff"
    elif 0.4 < value <= 0.7: return "#ffcccc"
    elif 0.7 < value <= 1.0: return "#ff9999"
    elif 1.0 < value <= 2.3: return "#ff6666"
    elif 2.3 < value <= 2.6: return "#ff0000"
    else: return "#cccccc"

def get_color_dongtan(value):
    try: value = float(value)
    except: return "#cccccc"
    if 0.0 < value <= 0.4: return "#ffffff"
    elif 0.4 < value <= 1.25: return "#ff9999"
    elif 1.25 < value <= 2.0: return "#ff6666"
    elif 2.0 < value <= 2.3: return "#ff0000"
    else: return "#cccccc"

if selected_area == "발안일반산업단지":
    get_color = get_color_balan
elif selected_area == "향남제약일반산업단지":
    get_color = get_color_hyangnam
elif selected_area == "동탄도시첨단산업단지":
    get_color = get_color_dongtan

# ---- 메인 본문 ----
st.markdown("<h1 style='text-align:center; margin-bottom:1.5rem;'>📊 산업단지 화재 위험도 맵</h1>", unsafe_allow_html=True)
st.markdown(f"""
<div style='text-align:center; font-size:1.1rem; margin-bottom:1.5rem;'>
선택한 산업단지의 화재 위험도 등급을 위성지도와 함께 한눈에 제공합니다.<br>
위험도 수치는 각 구역별로 지도에 표시되며, 분석 결과는 좌측에서 확인하세요.<br>
</div>
""", unsafe_allow_html=True)

# ---- GeoJSON 처리 ----
try:
    gdf = gpd.read_file(geojson_path)
    if gdf.crs is not None and gdf.crs.to_string() != "EPSG:4326":
        gdf = gdf.to_crs(epsg=4326)
except Exception as e:
    st.error(f"GeoJSON 파일을 읽는 중 오류 발생: {e}")
    st.stop()

center = [gdf.geometry.centroid.y.mean(), gdf.geometry.centroid.x.mean()]
m = folium.Map(location=center, zoom_start=11)
folium.TileLayer(
    tiles="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}",
    attr="Tiles © Esri",
    name="Esri World Imagery",
    overlay=False,
    control=True
).add_to(m)

# ---- 스타일 함수 ----
def style_callback(feature):
    value = feature["properties"].get(last_property_col)
    try: value = float(value)
    except: return {"color": "black", "weight": 1, "fillColor": "#cccccc", "fillOpacity": 0.1}
    color = get_color(value)
    return {"color": "black", "weight": 1, "fillColor": color, "fillOpacity": 0.7}

def no_style_callback(feature):
    return {"color": "black", "weight": 1, "fillColor": "#cccccc", "fillOpacity": 0.4}

style_func = style_callback if use_color else no_style_callback

layer = folium.GeoJson(
    data=gdf.to_json(),
    name="산업단지 위험도",
    style_function=style_func,
    tooltip=folium.GeoJsonTooltip(fields=[last_property_col], aliases=["위험도:"], localize=True)
).add_to(m)
m.fit_bounds(layer.get_bounds())

# ---- 위험도 수치 ----
if use_color:
    for idx, row in gdf.iterrows():
        value = row[last_property_col]
        try:
            value_disp = round(float(value), 2)
        except:
            value_disp = value
        centroid = row["geometry"].centroid
        icon = DivIcon(
            icon_size=(60, 20),
            icon_anchor=(30, 10),
            html=f"<div style='font-size: 15pt; color: white; font-weight: bold; text-shadow: 2px 2px 4px black; z-index: 1000;'>{value_disp}</div>"
        )
        folium.Marker(location=[centroid.y, centroid.x], icon=icon).add_to(m)

# --- 버퍼 분석 처리 ---
if show_buffer:
    try:
        buffer_gdf = gpd.read_file(buffer_geojson_path)
        if buffer_gdf.crs is not None and buffer_gdf.crs.to_string() != "EPSG:4326":
            buffer_gdf = buffer_gdf.to_crs(epsg=4326)
        buffer_layer = folium.GeoJson(
            data=buffer_gdf.to_json(),
            name="버퍼 분석",
            style_function=lambda feature: {
                "fillColor": "#3388ff",
                "color": "#3388ff",
                "weight": 2,
                "fillOpacity": 0.2
            },
            tooltip=folium.GeoJsonTooltip(fields=[], aliases=[], localize=True)
        )
        buffer_layer.add_to(m)
    except Exception as e:
        st.error(f"버퍼 분석 GeoJSON 파일을 읽는 중 오류 발생: {e}")

# ---- folium LayerControl ----
folium.LayerControl().add_to(m)

# --- GPT 구역별 화재위험도 분석 프롬프트 시나리오 ---
df_csv = pd.read_csv(csv_path, encoding="utf-8")

output = st_folium(m, use_container_width=True, height=700)

clicked_id = None
if output and output.get("last_active_drawing"):
    props = output["last_active_drawing"]["properties"]
    clicked_id = props.get("id")

if clicked_id is not None:
    row = df_csv[df_csv["id"] == int(clicked_id)]
    if not row.empty:
        row = row.iloc[0]
        prompt = f"""
        당신은 산업단지 내 구역별 위험요인을 보고 분석하는 유능한 데이터 분석가입니다.
        다음은 {selected_area} {clicked_id}번 구역의 위험요인 분석 결과입니다.
        - 위험물회사개수: {row['위험물회사개수']}
        - 건물밀도: {row['건물밀도']}
        - 노후건물비율: {row['노후건물비율']}
        - 위험시설물: {row['위험시설물']}
        - 소방차접근성: {row['소방차접근성']}
        - 소방용수시설: {row['소방용수시설']}
        - 소방서및119안전센터: {row['소방서및119안전센터']}
        - 최종스코어링(위험도): {row['최종스코어링']}

        위 수치들은 각 구역별 위험도를 측정할 때 사용된 feature와 위험 수준 분류 결과입니다.
        각 클래스 분류는 5가지로 나뉘며 5가 가장 큰 (가장 위험한) 값이고, 1이 가장 작은 (가장 안전한) 값으로 분류되어 있습니다.
        강조하지만 이는 개수가 아닌 위험 수준입니다.
        각 feature의 특성과 클래스 분류 값을 고려하여 각 구역별 위험도 분석을 진행하려 합니다.
        모든 feature를 고려한 최종 분석 결과를 전문성있고 정확하게 작성하며, 1~2 줄로 요약해주세요.
        이 때, 생성되는 요약문에는 수치를 제시하지말고 이에 따른 결과를 제시해주세요. 예를 들어, 위험 수준이 5라면 "매우 높음", 4는 "높음", 3은 "보통", 2는 "낮음", 1은 "매우 낮음"입니다.
        중요한 특성 (위험 수준이 높은)을 더 집중적으로 분석해주세요.
        """
        if st.button(f"🔥 구역 {clicked_id} 화재 위험도 요약"):
            with st.spinner(f"구역 {clicked_id} AI 분석 결과 생성 중..."):
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=300,
                    temperature=0.7
                )
                summary = response.choices[0].message.content.strip()
            st.markdown("#### 📋 화재 위험도 요약 결과")
            st.success(summary)
    else:
        st.info("CSV에서 해당 구역의 위험요인 데이터를 찾을 수 없습니다.")
