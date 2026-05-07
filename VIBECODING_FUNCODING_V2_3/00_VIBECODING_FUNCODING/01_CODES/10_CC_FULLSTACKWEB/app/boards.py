"""
Board management module for AICOM community service.
Handles board CRUD operations and permissions.
"""

from typing import Optional, List, Literal
from datetime import datetime
from uuid import UUID
from pydantic import BaseModel, Field, field_validator
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
import re
import unicodedata
import logging

from .auth import get_current_user, csrf_protect
from .database import db
from .config import settings

logger = logging.getLogger(__name__)

# Setup templates
templates_dir = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(templates_dir))

# Add date filter
from datetime import datetime as dt

def format_date(value):
    """Format datetime to Korean format"""
    if isinstance(value, str):
        try:
            value = dt.fromisoformat(value.replace('Z', '+00:00'))
        except:
            return value
    
    now = dt.now(value.tzinfo if hasattr(value, 'tzinfo') else None)
    diff = now - value
    
    if diff.days == 0:
        if diff.seconds < 60:
            return "방금 전"
        elif diff.seconds < 3600:
            return f"{diff.seconds // 60}분 전"
        else:
            return f"{diff.seconds // 3600}시간 전"
    elif diff.days == 1:
        return "어제"
    elif diff.days < 7:
        return f"{diff.days}일 전"
    else:
        return value.strftime("%Y.%m.%d")

templates.env.filters["date"] = format_date

# Board permission types
PermissionType = Literal["all", "member", "admin"]

# Korean to English transliteration for slug generation
KOREAN_TO_ENGLISH = {
    '가': 'ga', '각': 'gak', '간': 'gan', '갈': 'gal', '감': 'gam', '갑': 'gap', '갓': 'gat', '강': 'gang',
    '개': 'gae', '객': 'gaek', '거': 'geo', '건': 'geon', '걸': 'geol', '검': 'geom', '겁': 'geop', '게': 'ge',
    '겨': 'gyeo', '격': 'gyeok', '견': 'gyeon', '결': 'gyeol', '겸': 'gyeom', '겹': 'gyeop', '경': 'gyeong',
    '계': 'gye', '고': 'go', '곡': 'gok', '곤': 'gon', '골': 'gol', '곰': 'gom', '곱': 'gop', '곳': 'got',
    '공': 'gong', '과': 'gwa', '곽': 'gwak', '관': 'gwan', '괄': 'gwal', '광': 'gwang', '괘': 'gwae',
    '괴': 'goe', '교': 'gyo', '구': 'gu', '국': 'guk', '군': 'gun', '굴': 'gul', '굽': 'gup', '궁': 'gung',
    '권': 'gwon', '궐': 'gwol', '귀': 'gwi', '규': 'gyu', '균': 'gyun', '귤': 'gyul', '그': 'geu', '극': 'geuk',
    '근': 'geun', '글': 'geul', '금': 'geum', '급': 'geup', '긍': 'geung', '기': 'gi', '긴': 'gin', '길': 'gil',
    '김': 'gim', '깊': 'gip', '까': 'kka', '깍': 'kkak', '깐': 'kkan', '깔': 'kkal', '깜': 'kkam', '깝': 'kkap',
    '깡': 'kkang', '깨': 'kkae', '꺼': 'kkeo', '꺽': 'kkeok', '껀': 'kkeon', '껄': 'kkeol', '껍': 'kkeop',
    '께': 'kke', '껴': 'kkyeo', '꼬': 'kko', '꼭': 'kkok', '꼴': 'kkol', '꼼': 'kkom', '꼽': 'kkop', '꽁': 'kkong',
    '꽃': 'kkot', '꽈': 'kkwa', '꽉': 'kkwak', '꽌': 'kkwan', '꽝': 'kkwang', '꽤': 'kkwae', '꾀': 'kkoe',
    '꾸': 'kku', '꾹': 'kkuk', '꾼': 'kkun', '꿀': 'kkul', '꿈': 'kkum', '꿉': 'kkup', '꿍': 'kkung', '끄': 'kkeu',
    '끈': 'kkeun', '끊': 'kkeun', '끌': 'kkeul', '끓': 'kkeul', '끔': 'kkeum', '끗': 'kkeut', '끙': 'kkeung',
    '끝': 'kkeut', '나': 'na', '낙': 'nak', '난': 'nan', '날': 'nal', '남': 'nam', '납': 'nap', '낫': 'nat',
    '낭': 'nang', '낮': 'nat', '내': 'nae', '낵': 'naek', '낸': 'naen', '낼': 'nael', '냄': 'naem', '냅': 'naep',
    '냇': 'naet', '냉': 'naeng', '냐': 'nya', '냔': 'nyan', '냘': 'nyal', '냠': 'nyam', '냥': 'nyang', '너': 'neo',
    '넉': 'neok', '넌': 'neon', '널': 'neol', '넓': 'neol', '넘': 'neom', '넙': 'neop', '넛': 'neot', '넝': 'neong',
    '네': 'ne', '넥': 'nek', '넨': 'nen', '넬': 'nel', '넴': 'nem', '넵': 'nep', '넷': 'net', '넹': 'neng',
    '녀': 'nyeo', '녁': 'nyeok', '년': 'nyeon', '념': 'nyeom', '녑': 'nyeop', '녕': 'nyeong', '노': 'no',
    '녹': 'nok', '논': 'non', '놀': 'nol', '놈': 'nom', '놉': 'nop', '농': 'nong', '높': 'nop', '놓': 'no',
    '놔': 'nwa', '뇌': 'noe', '뇨': 'nyo', '뇩': 'nyok', '뇽': 'nyong', '누': 'nu', '눅': 'nuk', '눈': 'nun',
    '눌': 'nul', '눔': 'num', '눕': 'nup', '눙': 'nung', '눠': 'nwo', '눴': 'nwot', '뉘': 'nwi', '뉜': 'nwin',
    '뉴': 'nyu', '뉴스': 'nyuseu', '늄': 'nyum', '느': 'neu', '늑': 'neuk', '는': 'neun', '늘': 'neul', '늙': 'neuk',
    '늠': 'neum', '늡': 'neup', '능': 'neung', '늦': 'neut', '늪': 'neup', '늬': 'nui', '니': 'ni', '닉': 'nik',
    '닌': 'nin', '닐': 'nil', '님': 'nim', '닙': 'nip', '닛': 'nit', '닝': 'ning', '다': 'da', '닥': 'dak',
    '단': 'dan', '닫': 'dat', '달': 'dal', '닮': 'dam', '담': 'dam', '답': 'dap', '닷': 'dat', '당': 'dang',
    '대': 'dae', '댁': 'daek', '댄': 'daen', '댈': 'dael', '댐': 'daem', '댑': 'daep', '댓': 'daet', '댕': 'daeng',
    '더': 'deo', '덕': 'deok', '던': 'deon', '덜': 'deol', '덤': 'deom', '덥': 'deop', '덧': 'deot', '덩': 'deong',
    '데': 'de', '덱': 'dek', '덴': 'den', '델': 'del', '뎀': 'dem', '뎁': 'dep', '뎃': 'det', '뎅': 'deng',
    '뎌': 'dyeo', '뎬': 'dyeon', '도': 'do', '독': 'dok', '돈': 'don', '돋': 'dot', '돌': 'dol', '돔': 'dom',
    '돕': 'dop', '돗': 'dot', '동': 'dong', '돼': 'dwae', '되': 'doe', '된': 'doen', '될': 'doel', '됨': 'doem',
    '됩': 'doep', '두': 'du', '둑': 'duk', '둔': 'dun', '둘': 'dul', '둠': 'dum', '둡': 'dup', '둥': 'dung',
    '둬': 'dwo', '뒤': 'dwi', '뒷': 'dwit', '듀': 'dyu', '드': 'deu', '득': 'deuk', '든': 'deun', '들': 'deul',
    '듦': 'deum', '듬': 'deum', '듭': 'deup', '듯': 'deut', '등': 'deung', '디': 'di', '딕': 'dik', '딘': 'din',
    '딛': 'dit', '딜': 'dil', '딤': 'dim', '딥': 'dip', '딩': 'ding', '따': 'tta', '딱': 'ttak', '딴': 'ttan',
    '딸': 'ttal', '땀': 'ttam', '땅': 'ttang', '때': 'ttae', '땐': 'ttaen', '땔': 'ttael', '땜': 'ttaem',
    '땝': 'ttaep', '땡': 'ttaeng', '떄': 'ttae', '떠': 'tteo', '떡': 'tteok', '떤': 'tteon', '떨': 'tteol',
    '떰': 'tteom', '떱': 'tteop', '떳': 'tteot', '떴': 'tteot', '떵': 'tteong', '떼': 'tte', '떽': 'ttek',
    '뗀': 'tten', '뗄': 'ttel', '뗌': 'ttem', '뗍': 'ttep', '뗏': 'ttet', '뗐': 'ttet', '뗑': 'tteng', '또': 'tto',
    '똑': 'ttok', '똔': 'tton', '똘': 'ttol', '똥': 'ttong', '뚜': 'ttu', '뚝': 'ttuk', '뚠': 'ttun', '뚤': 'ttul',
    '뚫': 'ttul', '뚱': 'ttung', '뛰': 'ttwi', '뛴': 'ttwin', '뛸': 'ttwil', '뜀': 'ttwim', '뜁': 'ttwip',
    '뜨': 'tteu', '뜩': 'tteuk', '뜬': 'tteun', '뜯': 'tteut', '뜰': 'tteul', '뜸': 'tteum', '뜹': 'tteup',
    '뜻': 'tteut', '띄': 'tti', '띈': 'ttin', '띌': 'ttil', '띔': 'ttim', '띕': 'ttip', '띠': 'tti', '띤': 'ttin',
    '띨': 'ttil', '띰': 'ttim', '띱': 'ttip', '띳': 'ttit', '띵': 'tting', '라': 'ra', '락': 'rak', '란': 'ran',
    '랄': 'ral', '람': 'ram', '랍': 'rap', '랏': 'rat', '랐': 'rat', '랑': 'rang', '래': 'rae', '랙': 'raek',
    '랜': 'raen', '랠': 'rael', '램': 'raem', '랩': 'raep', '랫': 'raet', '랬': 'raet', '랭': 'raeng', '랴': 'rya',
    '략': 'ryak', '량': 'ryang', '러': 'reo', '럭': 'reok', '런': 'reon', '럴': 'reol', '럼': 'reom', '럽': 'reop',
    '럿': 'reot', '렀': 'reot', '렁': 'reong', '레': 're', '렉': 'rek', '렌': 'ren', '렐': 'rel', '렘': 'rem',
    '렙': 'rep', '렛': 'ret', '렝': 'reng', '려': 'ryeo', '력': 'ryeok', '련': 'ryeon', '렬': 'ryeol', '렴': 'ryeom',
    '렵': 'ryeop', '렷': 'ryeot', '렸': 'ryeot', '령': 'ryeong', '례': 'rye', '로': 'ro', '록': 'rok', '론': 'ron',
    '롤': 'rol', '롬': 'rom', '롭': 'rop', '롯': 'rot', '롱': 'rong', '롸': 'rwa', '롹': 'rwak', '롼': 'rwan',
    '뢍': 'rwel', '뢨': 'rwom', '뢰': 'roe', '뢴': 'roen', '뢸': 'roel', '룃': 'rot', '룅': 'rong', '료': 'ryo',
    '룐': 'ryon', '룔': 'ryol', '룝': 'ryop', '룟': 'ryot', '룡': 'ryong', '루': 'ru', '룩': 'ruk', '룬': 'run',
    '룰': 'rul', '룸': 'rum', '룹': 'rup', '룻': 'rut', '룽': 'rung', '뤄': 'rwo', '뤘': 'rwot', '뤠': 'rwe',
    '뤼': 'rwi', '뤽': 'rwik', '륀': 'rwin', '륄': 'rwil', '륌': 'rwim', '륏': 'rwit', '륑': 'rwing', '류': 'ryu',
    '륙': 'ryuk', '륜': 'ryun', '률': 'ryul', '륨': 'ryum', '륩': 'ryup', '륫': 'ryut', '륭': 'ryung', '르': 'reu',
    '륵': 'reuk', '른': 'reun', '를': 'reul', '름': 'reum', '릅': 'reup', '릇': 'reut', '릉': 'reung', '릊': 'reuk',
    '릋': 'reut', '릍': 'reup', '릎': 'reup', '리': 'ri', '릭': 'rik', '린': 'rin', '릴': 'ril', '림': 'rim',
    '립': 'rip', '릿': 'rit', '링': 'ring', '마': 'ma', '막': 'mak', '만': 'man', '많': 'man', '맏': 'mat',
    '말': 'mal', '맑': 'mak', '맘': 'mam', '맙': 'map', '맛': 'mat', '망': 'mang', '맞': 'mat', '맡': 'mat',
    '맣': 'mat', '매': 'mae', '맥': 'maek', '맨': 'maen', '맬': 'mael', '맴': 'maem', '맵': 'maep', '맷': 'maet',
    '맸': 'maet', '맹': 'maeng', '맺': 'maet', '먀': 'mya', '먁': 'myak', '먄': 'myan', '먈': 'myal', '먐': 'myam',
    '먕': 'myang', '머': 'meo', '먹': 'meok', '먼': 'meon', '멀': 'meol', '멈': 'meom', '멉': 'meop', '멋': 'meot',
    '멍': 'meong', '멎': 'meot', '메': 'me', '멕': 'mek', '멘': 'men', '멜': 'mel', '멤': 'mem', '멥': 'mep',
    '멧': 'met', '멨': 'met', '멩': 'meng', '며': 'myeo', '멱': 'myeok', '면': 'myeon', '멸': 'myeol', '몄': 'myeot',
    '명': 'myeong', '몇': 'myeot', '모': 'mo', '목': 'mok', '몫': 'mok', '몬': 'mon', '몰': 'mol', '몸': 'mom',
    '몹': 'mop', '못': 'mot', '몽': 'mong', '뫄': 'mwa', '뫈': 'mwal', '뫘': 'mwam', '뫙': 'mwap', '뫼': 'moe',
    '묀': 'moen', '묄': 'moel', '묍': 'moep', '묏': 'moet', '묑': 'moeng', '묘': 'myo', '묜': 'myon', '묠': 'myol',
    '묩': 'myop', '묫': 'myot', '무': 'mu', '묵': 'muk', '묶': 'muk', '문': 'mun', '묻': 'mut', '물': 'mul',
    '묽': 'mul', '뭄': 'mum', '뭅': 'mup', '뭇': 'mut', '뭉': 'mung', '뭍': 'mut', '뭏': 'mut', '뭐': 'mwo',
    '뭔': 'mwon', '뭘': 'mwol', '뭡': 'mwop', '뭣': 'mwot', '뭬': 'mwe', '뮈': 'mwi', '뮌': 'mwin', '뮐': 'mwil',
    '뮤': 'myu', '뮨': 'myun', '뮬': 'myul', '뮴': 'myum', '뮷': 'myut', '므': 'meu', '믄': 'meun', '믈': 'meul',
    '믐': 'meum', '믓': 'meut', '미': 'mi', '믹': 'mik', '민': 'min', '믿': 'mit', '밀': 'mil', '밂': 'mil',
    '밈': 'mim', '밉': 'mip', '밋': 'mit', '밌': 'mit', '밍': 'ming', '및': 'mit', '밑': 'mit', '바': 'ba',
    '박': 'bak', '밖': 'bak', '반': 'ban', '받': 'bat', '발': 'bal', '밝': 'bak', '밞': 'bak', '밟': 'bap',
    '밤': 'bam', '밥': 'bap', '밧': 'bat', '방': 'bang', '밭': 'bat', '배': 'bae', '백': 'baek', '밴': 'baen',
    '밸': 'bael', '뱀': 'baem', '뱁': 'baep', '뱃': 'baet', '뱄': 'baet', '뱅': 'baeng', '뱉': 'baet', '뱌': 'bya',
    '뱍': 'byak', '뱐': 'byan', '뱝': 'byap', '버': 'beo', '벅': 'beok', '번': 'beon', '벋': 'beot', '벌': 'beol',
    '벎': 'beol', '범': 'beom', '법': 'beop', '벗': 'beot', '벙': 'beong', '벚': 'beot', '베': 'be', '벡': 'bek',
    '벤': 'ben', '벧': 'bet', '벨': 'bel', '벰': 'bem', '벱': 'bep', '벳': 'bet', '벴': 'bet', '벵': 'beng',
    '벼': 'byeo', '벽': 'byeok', '변': 'byeon', '별': 'byeol', '볍': 'byeop', '볏': 'byeot', '볐': 'byeot',
    '병': 'byeong', '볕': 'byeot', '볘': 'bye', '볜': 'byel', '보': 'bo', '복': 'bok', '볶': 'bok', '본': 'bon',
    '볼': 'bol', '봄': 'bom', '봅': 'bop', '봇': 'bot', '봉': 'bong', '봐': 'bwa', '봔': 'bwan', '봤': 'bwat',
    '뵀': 'bwat', '뵈': 'boe', '뵉': 'boep', '뵌': 'boen', '뵐': 'boel', '뵘': 'boem', '뵙': 'boep', '뵤': 'byo',
    '뵨': 'byon', '부': 'bu', '북': 'buk', '분': 'bun', '붇': 'but', '불': 'bul', '붉': 'buk', '붊': 'buk',
    '붐': 'bum', '붑': 'bup', '붓': 'but', '붕': 'bung', '붙': 'but', '붜': 'bwe', '붤': 'bwel', '붰': 'bwom',
    '붸': 'bui', '뷔': 'bwi', '뷕': 'bwik', '뷘': 'bwin', '뷜': 'bwil', '뷩': 'bwip', '뷰': 'byu', '뷴': 'byun',
    '뷸': 'byul', '븀': 'beum', '븃': 'beut', '븅': 'beung', '브': 'beu', '븍': 'beuk', '븐': 'beun', '블': 'beul',
    '븜': 'beum', '븝': 'beup', '븟': 'beut', '비': 'bi', '빅': 'bik', '빈': 'bin', '빌': 'bil', '빎': 'bil',
    '빔': 'bim', '빕': 'bip', '빗': 'bit', '빙': 'bing', '빚': 'bit', '빛': 'bit', '빠': 'ppa', '빡': 'ppak',
    '빤': 'ppan', '빨': 'ppal', '빪': 'ppam', '빰': 'ppam', '빱': 'ppap', '빳': 'ppat', '빴': 'ppat', '빵': 'ppang',
    '빻': 'ppat', '빼': 'ppae', '빽': 'ppaek', '뺀': 'ppaen', '뺄': 'ppael', '뺌': 'ppaem', '뺍': 'ppaep',
    '뺏': 'ppaet', '뺐': 'ppaet', '뺑': 'ppaeng', '뺘': 'ppae', '뺙': 'ppaek', '뺨': 'ppyam', '뻐': 'ppeo',
    '뻑': 'ppeok', '뻔': 'ppeon', '뻗': 'ppeot', '뻘': 'ppeol', '뻠': 'ppeom', '뻣': 'ppeot', '뻤': 'ppeot',
    '뻥': 'ppeong', '뻬': 'ppe', '뼁': 'ppek', '뼈': 'ppyeo', '뼉': 'ppyeok', '뼐': 'ppyen', '뼘': 'ppyel',
    '뼙': 'ppyep', '뼛': 'ppyet', '뼜': 'ppyet', '뼝': 'ppyeng', '뽀': 'ppo', '뽁': 'ppok', '뽄': 'ppon',
    '뽈': 'ppol', '뽐': 'ppom', '뽑': 'ppop', '뽕': 'ppong', '뾔': 'ppwol', '뾰': 'ppyo', '뿅': 'ppyong',
    '뿌': 'ppu', '뿍': 'ppuk', '뿐': 'ppun', '뿔': 'ppul', '뿜': 'ppum', '뿟': 'pput', '뿡': 'ppung',
    '쀼': 'ppwye', '쁘': 'ppeu', '쁜': 'ppeun', '쁠': 'ppeul', '쁨': 'ppeum', '쁩': 'ppeup', '삐': 'ppi',
    '삑': 'ppik', '삔': 'ppin', '삘': 'ppil', '삠': 'ppim', '삡': 'ppip', '삣': 'ppit', '삥': 'pping',
    '사': 'sa', '삭': 'sak', '삯': 'sak', '산': 'san', '삳': 'sat', '살': 'sal', '삵': 'sak', '삶': 'sam',
    '삷': 'sap', '삸': 'sap', '삼': 'sam', '삽': 'sap', '삿': 'sat', '샀': 'sat', '상': 'sang', '샅': 'sat',
    '새': 'sae', '색': 'saek', '샌': 'saen', '샐': 'sael', '샘': 'saem', '샙': 'saep', '샛': 'saet', '샜': 'saet',
    '생': 'saeng', '샤': 'sya', '샥': 'syak', '샨': 'syan', '샬': 'syal', '샴': 'syam', '샵': 'syap', '샷': 'syat',
    '샹': 'syang', '섀': 'syae', '섄': 'syaen', '섈': 'syael', '섐': 'syaem', '섕': 'syaeng', '서': 'seo',
    '석': 'seok', '섞': 'seok', '선': 'seon', '섣': 'seot', '설': 'seol', '섦': 'seol', '섧': 'seop', '섬': 'seom',
    '섭': 'seop', '섯': 'seot', '섰': 'seot', '성': 'seong', '섶': 'seop', '세': 'se', '섹': 'sek', '센': 'sen',
    '셀': 'sel', '셈': 'sem', '셉': 'sep', '셋': 'set', '셌': 'set', '셍': 'seng', '셔': 'syeo', '셕': 'syeok',
    '션': 'syeon', '셜': 'syeol', '셤': 'syeom', '셥': 'syeop', '셧': 'syeot', '셨': 'syeot', '셩': 'syeong',
    '셰': 'sye', '셴': 'syen', '셸': 'syel', '솅': 'syeng', '소': 'so', '속': 'sok', '솎': 'sot', '손': 'son',
    '솔': 'sol', '솖': 'sol', '솜': 'som', '솝': 'sop', '솟': 'sot', '송': 'song', '솥': 'sot', '솨': 'swa',
    '솩': 'swak', '솬': 'swan', '솰': 'swal', '솽': 'swang', '쇄': 'swae', '쇈': 'swaen', '쇌': 'swael',
    '쇔': 'swem', '쇗': 'swet', '쇘': 'swet', '쇠': 'soe', '쇤': 'soen', '쇨': 'soel', '쇰': 'soem', '쇱': 'soep',
    '쇳': 'soet', '쇼': 'syo', '쇽': 'syok', '숀': 'syon', '숄': 'syol', '숌': 'syom', '숍': 'syop', '숏': 'syot',
    '숑': 'syong', '수': 'su', '숙': 'suk', '순': 'sun', '숟': 'sut', '술': 'sul', '숨': 'sum', '숩': 'sup',
    '숫': 'sut', '숭': 'sung', '숯': 'sut', '숱': 'sut', '숲': 'sup', '숴': 'swo', '쉈': 'swet', '쉐': 'swe',
    '쉑': 'swek', '쉔': 'swen', '쉘': 'swel', '쉠': 'swem', '쉥': 'sweng', '쉬': 'swi', '쉭': 'swik', '쉰': 'swin',
    '쉴': 'swil', '쉼': 'swim', '쉽': 'swip', '쉿': 'swit', '슁': 'swing', '슈': 'syu', '슉': 'syuk', '슐': 'syul',
    '슘': 'syum', '슛': 'syut', '슝': 'syung', '스': 'seu', '슥': 'seuk', '슨': 'seun', '슬': 'seul', '슭': 'seup',
    '슯': 'seut', '슴': 'seum', '습': 'seup', '슷': 'seut', '승': 'seung', '시': 'si', '식': 'sik', '신': 'sin',
    '싣': 'sit', '실': 'sil', '싫': 'sil', '심': 'sim', '십': 'sip', '싯': 'sit', '싱': 'sing', '싶': 'sip',
    '싸': 'ssa', '싹': 'ssak', '싼': 'ssan', '쌀': 'ssal', '쌈': 'ssam', '쌉': 'ssap', '쌌': 'ssat', '쌍': 'ssang',
    '쌓': 'ssat', '쌔': 'ssae', '쌘': 'ssaen', '쌤': 'ssaem', '쌥': 'ssaep', '쌨': 'ssaet', '쌩': 'ssaeng',
    '써': 'sseo', '썩': 'sseok', '썬': 'sseon', '썰': 'sseol', '썲': 'sseom', '썸': 'sseom', '썹': 'sseop',
    '썼': 'sseot', '썽': 'sseong', '쎄': 'sse', '쎈': 'ssen', '쎌': 'ssel', '쏀': 'sson', '쏘': 'sso', '쏙': 'ssok',
    '쏜': 'sson', '쏟': 'ssot', '쏠': 'ssol', '쏢': 'ssom', '쏨': 'ssom', '쏩': 'ssop', '쏭': 'ssong', '쏴': 'sswa',
    '쏵': 'sswak', '쏸': 'sswan', '쐈': 'sswat', '쐐': 'sswae', '쐤': 'sswe', '쐬': 'sswe', '쐰': 'sswel',
    '쐴': 'sswem', '쐼': 'sswep', '쐽': 'sswet', '쑈': 'ssyo', '쑤': 'ssu', '쑥': 'ssuk', '쑨': 'ssun', '쑬': 'ssul',
    '쑴': 'ssum', '쑵': 'ssup', '쑹': 'ssung', '쒀': 'sswo', '쒔': 'sswe', '쒜': 'sswel', '쒸': 'sseu', '쒼': 'sseun',
    '쓱': 'sseuk', '쓴': 'sseun', '쓸': 'sseul', '쓺': 'sseum', '쓿': 'sseut', '씀': 'sseum', '씁': 'sseup',
    '씌': 'ssui', '씐': 'ssuin', '씔': 'ssuil', '씜': 'ssuim', '씨': 'ssi', '씩': 'ssik', '씬': 'ssin', '씰': 'ssil',
    '씸': 'ssim', '씹': 'ssip', '씻': 'ssit', '씽': 'ssing', '아': 'a', '악': 'ak', '안': 'an', '앉': 'an',
    '않': 'an', '알': 'al', '앍': 'ak', '앎': 'am', '앓': 'al', '암': 'am', '압': 'ap', '앗': 'at', '았': 'at',
    '앙': 'ang', '앝': 'at', '앞': 'ap', '애': 'ae', '액': 'aek', '앤': 'aen', '앨': 'ael', '앰': 'aem', '앱': 'aep',
    '앳': 'aet', '앴': 'aet', '앵': 'aeng', '야': 'ya', '약': 'yak', '얀': 'yan', '얄': 'yal', '얇': 'yal',
    '얌': 'yam', '얍': 'yap', '얏': 'yat', '양': 'yang', '얕': 'yat', '얗': 'yak', '얘': 'yae', '얜': 'yaen',
    '얠': 'yael', '얩': 'yaep', '어': 'eo', '억': 'eok', '언': 'eon', '얹': 'eon', '얻': 'eot', '얼': 'eol',
    '얽': 'eok', '얾': 'eom', '엄': 'eom', '업': 'eop', '없': 'eop', '엇': 'eot', '었': 'eot', '엉': 'eong',
    '엊': 'eot', '엌': 'eot', '엎': 'eop', '에': 'e', '엑': 'ek', '엔': 'en', '엘': 'el', '엠': 'em', '엡': 'ep',
    '엣': 'et', '엥': 'eng', '여': 'yeo', '역': 'yeok', '엮': 'yeok', '연': 'yeon', '열': 'yeol', '엳': 'yeot',
    '염': 'yeom', '엽': 'yeop', '엾': 'yeot', '엿': 'yeot', '였': 'yeot', '영': 'yeong', '옅': 'yeot', '옆': 'yeop',
    '옇': 'yeop', '예': 'ye', '옌': 'yen', '옐': 'yel', '옘': 'yem', '옙': 'yep', '옛': 'yet', '옜': 'yet',
    '오': 'o', '옥': 'ok', '온': 'on', '올': 'ol', '옭': 'ol', '옮': 'om', '옰': 'om', '옳': 'ol', '옴': 'om',
    '옵': 'op', '옷': 'ot', '옹': 'ong', '옻': 'ot', '와': 'wa', '왁': 'wak', '완': 'wan', '왈': 'wal', '왐': 'wam',
    '왑': 'wap', '왓': 'wat', '왔': 'wat', '왕': 'wang', '왜': 'wae', '왠': 'waen', '왬': 'waem', '왯': 'waet',
    '왱': 'waeng', '외': 'oe', '왼': 'oen', '왹': 'oek', '왽': 'oet', '욀': 'ol', '욈': 'yom', '욉': 'yop',
    '욋': 'yot', '욍': 'yong', '요': 'yo', '욕': 'yok', '욘': 'yon', '욜': 'yol', '욤': 'yom', '욥': 'yop',
    '욧': 'yot', '용': 'yong', '우': 'u', '욱': 'uk', '운': 'un', '울': 'ul', '욹': 'ul', '욺': 'um', '움': 'um',
    '웁': 'up', '웃': 'ut', '웅': 'ung', '워': 'wo', '웍': 'wok', '원': 'won', '월': 'wol', '웜': 'wom', '웝': 'wop',
    '웟': 'wot', '웠': 'wot', '웡': 'wong', '웨': 'we', '웩': 'wek', '웬': 'wen', '웰': 'wel', '웸': 'wem',
    '웹': 'wep', '웻': 'wet', '웽': 'weng', '위': 'wi', '윅': 'wik', '윈': 'win', '윌': 'wil', '윔': 'wim',
    '윕': 'wip', '윗': 'wit', '윙': 'wing', '유': 'yu', '육': 'yuk', '윤': 'yun', '율': 'yul', '윰': 'yum',
    '윱': 'yup', '윳': 'yut', '융': 'yung', '윷': 'yut', '으': 'eu', '윽': 'euk', '은': 'eun', '을': 'eul',
    '읊': 'eup', '음': 'eum', '읍': 'eup', '읏': 'eut', '응': 'eung', '읒': 'eup', '읓': 'eut', '읔': 'eum',
    '읕': 'eup', '읖': 'eut', '읗': 'eung', '의': 'ui', '읜': 'uik', '읠': 'uin', '읨': 'uim', '읫': 'uit',
    '이': 'i', '익': 'ik', '인': 'in', '일': 'il', '읽': 'ik', '읾': 'im', '잃': 'il', '임': 'im', '입': 'ip',
    '잇': 'it', '있': 'it', '잉': 'ing', '잊': 'it', '잎': 'ip', '자': 'ja', '작': 'jak', '잔': 'jan', '잖': 'jan',
    '잗': 'jat', '잘': 'jal', '잚': 'jal', '잠': 'jam', '잡': 'jap', '잣': 'jat', '잤': 'jat', '장': 'jang',
    '잦': 'jat', '재': 'jae', '잭': 'jaek', '잰': 'jaen', '잴': 'jael', '잼': 'jaem', '잽': 'jaep', '잿': 'jaet',
    '쟀': 'jaet', '쟁': 'jaeng', '쟈': 'jya', '쟉': 'jyak', '쟌': 'jyan', '쟎': 'jyal', '쟐': 'jyam', '쟘': 'jyal',
    '쟝': 'jyang', '쟤': 'jyae', '쟨': 'jyaen', '쟬': 'jyael', '쟴': 'jyaem', '쟸': 'jyaep', '쟹': 'jyaet',
    '저': 'jeo', '적': 'jeok', '전': 'jeon', '절': 'jeol', '젊': 'jeom', '점': 'jeom', '접': 'jeop', '젓': 'jeot',
    '정': 'jeong', '젖': 'jeot', '제': 'je', '젝': 'jek', '젠': 'jen', '젤': 'jel', '젬': 'jem', '젭': 'jep',
    '젯': 'jet', '젱': 'jeng', '져': 'jyeo', '젹': 'jyeok', '젼': 'jyeon', '졀': 'jyeol', '졈': 'jyeom', '졉': 'jyeop',
    '졌': 'jyeot', '졍': 'jyeong', '졔': 'jye', '조': 'jo', '족': 'jok', '존': 'jon', '졸': 'jol', '졺': 'jol',
    '좀': 'jom', '좁': 'jop', '좃': 'jot', '종': 'jong', '좆': 'jot', '좇': 'jot', '좉': 'jot', '좋': 'jo',
    '좌': 'jwa', '좍': 'jwak', '좔': 'jwal', '좝': 'jwap', '좟': 'jwat', '좡': 'jwang', '좨': 'jwae', '좼': 'jwael',
    '좽': 'jwaet', '죄': 'joe', '죈': 'joen', '죌': 'joel', '죔': 'joem', '죕': 'joep', '죗': 'joet', '죙': 'joeng',
    '죠': 'jyo', '죡': 'jyok', '죤': 'jyon', '죵': 'jyong', '주': 'ju', '죽': 'juk', '준': 'jun', '줄': 'jul',
    '줅': 'jul', '줆': 'jum', '줌': 'jum', '줍': 'jup', '줏': 'jut', '중': 'jung', '줘': 'jwo', '줬': 'jwot',
    '줴': 'jwe', '쥐': 'jwi', '쥑': 'jwik', '쥔': 'jwin', '쥘': 'jwil', '쥠': 'jwim', '쥡': 'jwip', '쥣': 'jwit',
    '쥬': 'jyu', '쥰': 'jyun', '쥴': 'jyul', '쥼': 'jyum', '즈': 'jeu', '즉': 'jeuk', '즌': 'jeun', '즐': 'jeul',
    '즘': 'jeum', '즙': 'jeup', '즛': 'jeut', '증': 'jeung', '지': 'ji', '직': 'jik', '진': 'jin', '짇': 'jit',
    '질': 'jil', '짊': 'jim', '짐': 'jim', '집': 'jip', '짓': 'jit', '징': 'jing', '짖': 'jit', '짙': 'jit',
    '짚': 'jip', '짜': 'jja', '짝': 'jjak', '짠': 'jjan', '짢': 'jjal', '짤': 'jjal', '짧': 'jjal', '짬': 'jjam',
    '짭': 'jjap', '짯': 'jjat', '짰': 'jjat', '짱': 'jjang', '째': 'jjae', '짹': 'jjaek', '짼': 'jjaen', '쨀': 'jjael',
    '쨈': 'jjaem', '쨉': 'jjaep', '쨋': 'jjaet', '쨌': 'jjaet', '쨍': 'jjaeng', '쨔': 'jjya', '쨘': 'jjyal',
    '쨩': 'jjyang', '쩌': 'jjeo', '쩍': 'jjeok', '쩐': 'jjeon', '쩔': 'jjeol', '쩜': 'jjeom', '쩝': 'jjeop',
    '쩟': 'jjeot', '쩠': 'jjeot', '쩡': 'jjeong', '쩨': 'jje', '쩬': 'jjen', '쪄': 'jjyeo', '쪘': 'jjyeol',
    '쪼': 'jjo', '쪽': 'jjok', '쫀': 'jjon', '쫄': 'jjol', '쫌': 'jjom', '쫍': 'jjop', '쫏': 'jjot', '쫑': 'jjong',
    '쫓': 'jjot', '쫘': 'jjwa', '쫙': 'jjwak', '쫠': 'jjwal', '쫬': 'jjwam', '쫴': 'jjoe', '쬈': 'jjoen',
    '쬐': 'jjoe', '쬔': 'jjoen', '쬘': 'jjoel', '쬠': 'jjoem', '쬡': 'jjoep', '쭁': 'jjung', '쭈': 'jju',
    '쭉': 'jjuk', '쭌': 'jjun', '쭐': 'jjul', '쭘': 'jjum', '쭙': 'jjup', '쭝': 'jjung', '쭤': 'jjwo', '쭸': 'jjwon',
    '쭹': 'jjwot', '쮜': 'jjwe', '쮸': 'jjyu', '쯔': 'jjeu', '쯤': 'jjeum', '쯧': 'jjeut', '쯩': 'jjeung',
    '찌': 'jji', '찍': 'jjik', '찐': 'jjin', '찔': 'jjil', '찜': 'jjim', '찝': 'jjip', '찡': 'jjing', '찢': 'jjit',
    '찧': 'jjit', '차': 'cha', '착': 'chak', '찬': 'chan', '찮': 'chan', '찰': 'chal', '참': 'cham', '찹': 'chap',
    '찻': 'chat', '찼': 'chat', '창': 'chang', '찾': 'chat', '채': 'chae', '책': 'chaek', '챈': 'chaen',
    '챌': 'chael', '챔': 'chaem', '챕': 'chaep', '챗': 'chaet', '챘': 'chaet', '챙': 'chaeng', '챠': 'chya',
    '챤': 'chyan', '챦': 'chyal', '챨': 'chyam', '챰': 'chyam', '챵': 'chyang', '처': 'cheo', '척': 'cheok',
    '천': 'cheon', '철': 'cheol', '첨': 'cheom', '첩': 'cheop', '첫': 'cheot', '첬': 'cheot', '청': 'cheong',
    '체': 'che', '첵': 'chek', '첸': 'chen', '첼': 'chel', '쳄': 'chem', '쳅': 'chep', '쳇': 'chet', '쳉': 'cheng',
    '쳐': 'chyeo', '쳔': 'chyeon', '쳤': 'chyeot', '쳬': 'chye', '쳰': 'chyen', '촁': 'chyop', '초': 'cho',
    '촉': 'chok', '촌': 'chon', '촐': 'chol', '촘': 'chom', '촙': 'chop', '촛': 'chot', '총': 'chong', '촤': 'chwa',
    '촨': 'chwan', '촬': 'chwal', '촹': 'chwang', '최': 'choe', '쵠': 'choem', '쵤': 'choel', '쵬': 'choem',
    '쵭': 'choep', '쵯': 'choet', '쵱': 'choeng', '쵸': 'chyo', '춈': 'chyon', '추': 'chu', '축': 'chuk',
    '춘': 'chun', '출': 'chul', '춤': 'chum', '춥': 'chup', '춧': 'chut', '충': 'chung', '춰': 'chwo', '췄': 'chwot',
    '췌': 'chwe', '췐': 'chwen', '취': 'chwi', '췬': 'chwin', '췰': 'chwil', '췸': 'chwim', '췹': 'chwip',
    '췻': 'chwit', '췽': 'chwing', '츄': 'chyu', '츈': 'chyun', '츌': 'chyul', '츔': 'chyum', '츙': 'chyung',
    '츠': 'cheu', '측': 'cheuk', '츤': 'cheun', '츨': 'cheul', '츰': 'cheum', '츱': 'cheup', '츳': 'cheut',
    '층': 'cheung', '치': 'chi', '칙': 'chik', '친': 'chin', '칟': 'chit', '칠': 'chil', '칡': 'chik', '침': 'chim',
    '칩': 'chip', '칫': 'chit', '칭': 'ching', '카': 'ka', '칵': 'kak', '칸': 'kan', '칼': 'kal', '캄': 'kam',
    '캅': 'kap', '캇': 'kat', '캉': 'kang', '캐': 'kae', '캑': 'kaek', '캔': 'kaen', '캘': 'kael', '캠': 'kaem',
    '캡': 'kaep', '캣': 'kaet', '캤': 'kaet', '캥': 'kaeng', '캬': 'kya', '캭': 'kyak', '컁': 'kyal', '커': 'keo',
    '컥': 'keok', '컨': 'keon', '컫': 'keot', '컬': 'keol', '컴': 'keom', '컵': 'keop', '컷': 'keot', '컸': 'keot',
    '컹': 'keong', '케': 'ke', '켁': 'kek', '켄': 'ken', '켈': 'kel', '켐': 'kem', '켑': 'kep', '켓': 'ket',
    '켕': 'keng', '켜': 'kyeo', '켠': 'kyeon', '켤': 'kyeol', '켬': 'kyeom', '켭': 'kyeop', '켯': 'kyeot',
    '켰': 'kyeot', '켱': 'kyeong', '켸': 'kye', '코': 'ko', '콕': 'kok', '콘': 'kon', '콜': 'kol', '콤': 'kom',
    '콥': 'kop', '콧': 'kot', '콩': 'kong', '콰': 'kwa', '콱': 'kwak', '콴': 'kwan', '콸': 'kwal', '쾀': 'kwam',
    '쾅': 'kwang', '쾌': 'kwae', '쾡': 'kwaeng', '쾨': 'koe', '쾰': 'koel', '쿄': 'kyo', '쿠': 'ku', '쿡': 'kuk',
    '쿤': 'kun', '쿨': 'kul', '쿰': 'kum', '쿱': 'kup', '쿳': 'kut', '쿵': 'kung', '쿼': 'kwo', '퀀': 'kwon',
    '퀄': 'kwol', '퀑': 'kwong', '퀘': 'kwe', '퀭': 'kweng', '퀴': 'kwi', '퀵': 'kwik', '퀸': 'kwin', '퀼': 'kwil',
    '큄': 'kwim', '큅': 'kwip', '큇': 'kwit', '큉': 'kwing', '큐': 'kyu', '큔': 'kyun', '큘': 'kyul', '큠': 'kyum',
    '크': 'keu', '큭': 'keuk', '큰': 'keun', '클': 'keul', '큼': 'keum', '큽': 'keup', '킁': 'keung', '키': 'ki',
    '킥': 'kik', '킨': 'kin', '킬': 'kil', '킴': 'kim', '킵': 'kip', '킷': 'kit', '킹': 'king', '타': 'ta',
    '탁': 'tak', '탄': 'tan', '탈': 'tal', '탉': 'tak', '탐': 'tam', '탑': 'tap', '탓': 'tat', '탔': 'tat',
    '탕': 'tang', '태': 'tae', '택': 'taek', '탠': 'taen', '탤': 'tael', '탬': 'taem', '탭': 'taep', '탯': 'taet',
    '탰': 'taet', '탱': 'taeng', '탸': 'tya', '턍': 'tyak', '터': 'teo', '턱': 'teok', '턴': 'teon', '털': 'teol',
    '텀': 'teom', '텁': 'teop', '텃': 'teot', '텄': 'teot', '텅': 'teong', '테': 'te', '텍': 'tek', '텐': 'ten',
    '텔': 'tel', '템': 'tem', '텝': 'tep', '텟': 'tet', '텡': 'teng', '텨': 'tyeo', '텬': 'tyeon', '텼': 'tyeot',
    '톄': 'tye', '톈': 'tyen', '토': 'to', '톡': 'tok', '톤': 'ton', '톨': 'tol', '톰': 'tom', '톱': 'top',
    '톳': 'tot', '통': 'tong', '톺': 'top', '톼': 'tol', '퇀': 'tom', '퇘': 'twae', '퇴': 'toe', '퇸': 'toen',
    '툇': 'toet', '툉': 'toeng', '툐': 'twe', '툔': 'twen', '툘': 'twel', '툠': 'twem', '툡': 'twep', '툣': 'twet',
    '툥': 'tweng', '투': 'tu', '툭': 'tuk', '툰': 'tun', '툴': 'tul', '툼': 'tum', '툽': 'tup', '툿': 'tut',
    '퉁': 'tung', '퉈': 'two', '퉜': 'twol', '퉤': 'twe', '튀': 'twi', '튄': 'twin', '튈': 'twil', '튐': 'twim',
    '튑': 'twip', '튕': 'twing', '튜': 'tyu', '튠': 'tyun', '튤': 'tyul', '튬': 'tyum', '튱': 'tyung', '트': 'teu',
    '특': 'teuk', '튼': 'teun', '튿': 'teut', '틀': 'teul', '틂': 'teul', '틈': 'teum', '틉': 'teup', '틋': 'teut',
    '틔': 'tui', '틘': 'tuin', '틜': 'tuil', '틤': 'tuim', '틥': 'tuip', '티': 'ti', '틱': 'tik', '틴': 'tin',
    '틸': 'til', '팀': 'tim', '팁': 'tip', '팃': 'tit', '팅': 'ting', '파': 'pa', '팍': 'pak', '팎': 'pak',
    '판': 'pan', '팔': 'pal', '팖': 'pal', '팜': 'pam', '팝': 'pap', '팟': 'pat', '팠': 'pat', '팡': 'pang',
    '팥': 'pat', '패': 'pae', '팩': 'paek', '팬': 'paen', '팰': 'pael', '팸': 'paem', '팹': 'paep', '팻': 'paet',
    '팼': 'paet', '팽': 'paeng', '퍄': 'pya', '퍅': 'pyak', '퍼': 'peo', '퍽': 'peok', '펀': 'peon', '펄': 'peol',
    '펌': 'peom', '펍': 'peop', '펏': 'peot', '펐': 'peot', '펑': 'peong', '페': 'pe', '펙': 'pek', '펜': 'pen',
    '펠': 'pel', '펨': 'pem', '펩': 'pep', '펫': 'pet', '펭': 'peng', '펴': 'pyeo', '편': 'pyeon', '펼': 'pyeol',
    '폄': 'pyeom', '폅': 'pyeop', '폈': 'pyeot', '평': 'pyeong', '폐': 'pye', '폔': 'pyen', '폘': 'pyel',
    '폡': 'pyep', '폣': 'pyet', '포': 'po', '폭': 'pok', '폰': 'pon', '폴': 'pol', '폼': 'pom', '폽': 'pop',
    '폿': 'pot', '퐁': 'pong', '퐈': 'pwa', '퐉': 'pwak', '퐝': 'pwap', '퐤': 'pwae', '퐨': 'pwaen', '퐬': 'pwael',
    '퐴': 'pwaem', '퐵': 'pwaep', '퐷': 'pwaet', '퐹': 'pwaeng', '표': 'pyo', '푠': 'pyol', '푤': 'pyom', '푭': 'pyop',
    '푯': 'pyot', '푱': 'pyong', '푸': 'pu', '푹': 'puk', '푼': 'pun', '푿': 'put', '풀': 'pul', '풂': 'pul',
    '품': 'pum', '풉': 'pup', '풋': 'put', '풍': 'pung', '풔': 'pwo', '풩': 'pwop', '퓌': 'pwe', '퓐': 'pwen',
    '퓔': 'pwel', '퓜': 'pwem', '퓟': 'pwet', '퓨': 'pyu', '퓬': 'pyun', '퓰': 'pyul', '퓸': 'pyum', '퓻': 'pyut',
    '퓽': 'pyung', '프': 'peu', '픈': 'peun', '플': 'peul', '픔': 'peum', '픕': 'peup', '픗': 'peut', '피': 'pi',
    '픽': 'pik', '핀': 'pin', '필': 'pil', '핍': 'pip', '핏': 'pit', '핑': 'ping', '하': 'ha', '학': 'hak',
    '한': 'han', '할': 'hal', '핥': 'hal', '함': 'ham', '합': 'hap', '핫': 'hat', '항': 'hang', '해': 'hae',
    '핵': 'haek', '핸': 'haen', '핼': 'hael', '햄': 'haem', '햅': 'haep', '햇': 'haet', '했': 'haet', '행': 'haeng',
    '햐': 'hya', '향': 'hyang', '허': 'heo', '헉': 'heok', '헌': 'heon', '헐': 'heol', '헒': 'heol', '험': 'heom',
    '헙': 'heop', '헛': 'heot', '헝': 'heong', '헤': 'he', '헥': 'hek', '헨': 'hen', '헬': 'hel', '헴': 'hem',
    '헵': 'hep', '헷': 'het', '헹': 'heng', '혀': 'hyeo', '혁': 'hyeok', '현': 'hyeon', '혈': 'hyeol', '혐': 'hyeom',
    '협': 'hyeop', '혓': 'hyeot', '혔': 'hyeot', '형': 'hyeong', '혜': 'hye', '혠': 'hyen', '혤': 'hyel',
    '혭': 'hyep', '호': 'ho', '혹': 'hok', '혼': 'hon', '홀': 'hol', '홅': 'hol', '홈': 'hom', '홉': 'hop',
    '홋': 'hot', '홍': 'hong', '홑': 'hot', '화': 'hwa', '확': 'hwak', '환': 'hwan', '활': 'hwal', '홧': 'hwat',
    '황': 'hwang', '홰': 'hwae', '홱': 'hwaek', '홴': 'hwaen', '횃': 'hwaet', '횅': 'hwaeng', '회': 'hoe',
    '획': 'hoek', '횐': 'hoen', '횔': 'hoel', '횝': 'hoep', '횟': 'hoet', '횡': 'hoeng', '효': 'hyo', '횬': 'hyon',
    '횰': 'hyol', '횹': 'hyop', '횻': 'hyot', '후': 'hu', '훅': 'huk', '훈': 'hun', '훌': 'hul', '훑': 'hul',
    '훔': 'hum', '훕': 'hup', '훗': 'hut', '훙': 'hung', '훠': 'hwo', '훤': 'hwon', '훨': 'hwol', '훰': 'hwom',
    '훵': 'hwop', '훼': 'hwe', '훽': 'hwek', '휀': 'hwen', '휄': 'hwel', '휑': 'hweng', '휘': 'hwi', '휙': 'hwik',
    '휜': 'hwin', '휠': 'hwil', '휨': 'hwim', '휩': 'hwip', '휫': 'hwit', '휭': 'hwing', '휴': 'hyu', '휵': 'hyuk',
    '휸': 'hyun', '휼': 'hyul', '흄': 'hyum', '흇': 'hyut', '흉': 'hyung', '흐': 'heu', '흑': 'heuk', '흔': 'heun',
    '흖': 'heut', '흗': 'heut', '흘': 'heul', '흙': 'heuk', '흠': 'heum', '흡': 'heup', '흣': 'heut', '흥': 'heung',
    '흩': 'heut', '희': 'hui', '흰': 'huin', '흴': 'huil', '흼': 'huim', '흽': 'huip', '힁': 'hing', '히': 'hi',
    '힉': 'hik', '힌': 'hin', '힐': 'hil', '힘': 'him', '힙': 'hip', '힛': 'hit', '힝': 'hing'
}


def generate_slug(name: str) -> str:
    """Generate slug from Korean or English name"""
    # Remove special characters and convert to lowercase
    slug = re.sub(r'[^\w\s-]', '', name.lower())
    
    # Convert Korean characters to English
    result = []
    for char in slug:
        if char in KOREAN_TO_ENGLISH:
            result.append(KOREAN_TO_ENGLISH[char])
        elif ord('가') <= ord(char) <= ord('힣'):
            # Handle Korean characters not in the mapping
            # Decompose and take the first consonant
            result.append('k')  # Default fallback
        else:
            result.append(char)
    
    # Join and clean up
    slug = ''.join(result)
    slug = re.sub(r'[-\s]+', '-', slug)
    slug = slug.strip('-')
    
    return slug


# Schemas
class BoardCreate(BaseModel):
    """Schema for creating a board"""
    name: str = Field(..., min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    can_write: PermissionType = "member"
    can_read: PermissionType = "all"
    display_order: int = 0
    
    @field_validator('slug')
    def validate_slug(cls, v):
        if v:
            # Ensure slug is URL-safe
            if not re.match(r'^[a-z0-9_-]+$', v):
                raise ValueError("Slug must contain only lowercase letters, numbers, underscores, and hyphens")
        return v


class BoardUpdate(BaseModel):
    """Schema for updating a board"""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = None
    icon: Optional[str] = Field(None, max_length=50)
    can_write: Optional[PermissionType] = None
    can_read: Optional[PermissionType] = None
    display_order: Optional[int] = None
    is_active: Optional[bool] = None
    
    @field_validator('slug')
    def validate_slug(cls, v):
        if v:
            if not re.match(r'^[a-z0-9_-]+$', v):
                raise ValueError("Slug must contain only lowercase letters, numbers, underscores, and hyphens")
        return v


class BoardResponse(BaseModel):
    """Schema for board response"""
    id: str
    name: str
    slug: str
    description: Optional[str]
    icon: Optional[str]
    can_write: PermissionType
    can_read: PermissionType
    display_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime


class BoardPermissions(BaseModel):
    """Schema for board permissions response"""
    can_read: bool
    can_write: bool
    is_admin: bool


# Helper functions
def check_read_permission(board: dict, user: Optional[dict]) -> bool:
    """Check if user has read permission for a board"""
    if board["can_read"] == "all":
        return True
    elif board["can_read"] == "member":
        return user is not None
    elif board["can_read"] == "admin":
        return user is not None and user.get("is_admin", False)
    return False


def check_write_permission(board: dict, user: Optional[dict]) -> bool:
    """Check if user has write permission for a board"""
    if board["can_write"] == "all":
        return True
    elif board["can_write"] == "member":
        return user is not None
    elif board["can_write"] == "admin":
        return user is not None and user.get("is_admin", False)
    return False


def get_board_by_id_or_slug(board_id: str) -> Optional[dict]:
    """Get board by ID or slug"""
    # Try UUID first
    try:
        UUID(board_id)
        boards = db.select("boards", filters={"id": board_id})
    except ValueError:
        # Not a UUID, try slug
        boards = db.select("boards", filters={"slug": board_id})
    
    if boards and boards[0]["is_active"]:
        return boards[0]
    return None


# Router
router = APIRouter(prefix="/api/boards", tags=["boards"])


@router.post("/create", response_model=BoardResponse, status_code=201, dependencies=[Depends(csrf_protect)])
async def create_board(
    request: Request,
    board_data: BoardCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new board (admin only)"""
    # CSRF is already handled by dependency injection in auth.py
    
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Only administrators can create boards"
        )
    
    # Generate slug if not provided
    if not board_data.slug:
        board_data.slug = generate_slug(board_data.name)
    
    # Check if slug already exists
    existing = db.select("boards", filters={"slug": board_data.slug})
    if existing:
        raise HTTPException(
            status_code=409,
            detail=f"Board with slug '{board_data.slug}' already exists"
        )
    
    # Create board
    board = db.insert("boards", board_data.model_dump(exclude_none=True))
    
    return BoardResponse(**board)


@router.get("", response_model=List[BoardResponse])
async def list_boards(request: Request):
    """List all active boards"""
    # Get current user (optional)
    user = getattr(request.state, "user", None)
    
    # Get all active boards
    boards = db.select(
        "boards",
        filters={"is_active": True}
    )
    
    # Sort by display_order
    boards.sort(key=lambda x: x["display_order"])
    
    # Filter by read permission
    accessible_boards = []
    for board in boards:
        if check_read_permission(board, user):
            accessible_boards.append(BoardResponse(**board))
    
    return accessible_boards


@router.get("/{board_id}", response_model=BoardResponse)
async def get_board(
    request: Request,
    board_id: str
):
    """Get board details by ID or slug"""
    # Get current user (optional)
    user = getattr(request.state, "user", None)
    
    # Get board
    board = get_board_by_id_or_slug(board_id)
    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board not found"
        )
    
    # Check read permission
    if not check_read_permission(board, user):
        raise HTTPException(
            status_code=403,
            detail="You don't have permission to view this board"
        )
    
    return BoardResponse(**board)


@router.patch("/{board_id}/update", response_model=BoardResponse, dependencies=[Depends(csrf_protect)])
async def update_board(
    request: Request,
    board_id: str,
    board_data: BoardUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update board information (admin only)"""
    # CSRF is already handled by dependency injection in auth.py
    
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Only administrators can update boards"
        )
    
    # Get board
    board = get_board_by_id_or_slug(board_id)
    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board not found"
        )
    
    # Check if new slug conflicts
    if board_data.slug and board_data.slug != board["slug"]:
        existing = db.select("boards", filters={"slug": board_data.slug})
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Board with slug '{board_data.slug}' already exists"
            )
    
    # Update board
    update_data = board_data.model_dump(exclude_none=True)
    if update_data:
        board = db.update("boards", update_data, {"id": board["id"]})
    
    return BoardResponse(**board)


@router.delete("/{board_id}/delete", dependencies=[Depends(csrf_protect)])
async def delete_board(
    request: Request,
    board_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Soft delete a board (admin only)"""
    # CSRF is already handled by dependency injection in auth.py
    
    # Check authentication
    if not current_user:
        raise HTTPException(
            status_code=401,
            detail="Authentication required"
        )
    
    # Check admin permission
    if not current_user.get("is_admin", False):
        raise HTTPException(
            status_code=403,
            detail="Only administrators can delete boards"
        )
    
    # Get board
    board = get_board_by_id_or_slug(board_id)
    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board not found"
        )
    
    # Soft delete (set is_active to false)
    db.update("boards", {"is_active": False}, {"id": board["id"]})
    
    return {"message": "Board deleted successfully"}


@router.get("/{board_id}/permissions", response_model=BoardPermissions)
async def check_board_permissions(
    request: Request,
    board_id: str
):
    """Check user permissions for a board"""
    # Get current user (optional) - use get_current_user to get full profile
    user = get_current_user(request)
    
    # Get board
    board = get_board_by_id_or_slug(board_id)
    if not board:
        raise HTTPException(
            status_code=404,
            detail="Board not found"
        )
    
    # Check permissions
    return BoardPermissions(
        can_read=check_read_permission(board, user),
        can_write=check_write_permission(board, user),
        is_admin=user is not None and user.get("is_admin", False)
    )


@router.get("/{board_slug}/posts-html", response_class=HTMLResponse)
async def get_board_posts_html(
    request: Request,
    board_slug: str,
    page: int = 1,
    q: str = None,
    search_type: str = "all"
):
    """Get board posts as HTML for HTMX requests"""
    # Get current user
    user = get_current_user(request)
    
    # Get board
    board = get_board_by_id_or_slug(board_slug)
    if not board:
        return HTMLResponse(
            content='<div class="p-8 text-center text-red-500">게시판을 찾을 수 없습니다.</div>',
            status_code=404
        )
    
    # Check read permission
    if not check_read_permission(board, user):
        return HTMLResponse(
            content='<div class="p-8 text-center text-red-500">이 게시판을 볼 권한이 없습니다.</div>',
            status_code=403
        )
    
    # Check write permission
    can_write = check_write_permission(board, user)
    
    # Get posts with pagination
    per_page = 20
    offset = (page - 1) * per_page
    
    # Search posts if query provided
    if q and q.strip():
        try:
            # Use PostgreSQL full-text search via RPC
            search_results = db.rpc("search_board_posts", {
                "board_id_param": board["id"],
                "search_query": q,
                "search_type": search_type
            })
            
            # Apply pagination to search results
            total_count = len(search_results)
            posts = search_results[offset:offset + per_page]
        except Exception as e:
            # Fallback to ILIKE search if RPC fails
            logger.error(f"Full-text search failed: {e}, falling back to ILIKE")
            query = db.client.table("posts").select("*")
            query = query.eq("board_id", board["id"]).eq("is_active", True)
            
            # Apply ILIKE search filter
            if search_type == "title":
                query = query.ilike("title", f"%{q}%")
            elif search_type == "content":
                query = query.ilike("content", f"%{q}%")
            else:
                # Search in both title and content
                query = query.or_(f"title.ilike.%{q}%,content.ilike.%{q}%")
            
            # Order and paginate
            query = query.order("is_pinned.desc.nullslast,created_at.desc.nullslast,id.desc.nullslast")
            query = query.limit(per_page).offset(offset)
            
            response = query.execute()
            posts = response.data
            
            # Get total count
            count_query = db.client.table("posts").select("*", count="exact")
            count_query = count_query.eq("board_id", board["id"]).eq("is_active", True)
            
            if search_type == "title":
                count_query = count_query.ilike("title", f"%{q}%")
            elif search_type == "content":
                count_query = count_query.ilike("content", f"%{q}%")
            else:
                count_query = count_query.or_(f"title.ilike.%{q}%,content.ilike.%{q}%")
            
            count_response = count_query.execute()
            total_count = count_response.count
    else:
        # Get all posts without search
        # Use Supabase client directly for better ordering control
        query = db.client.table("posts").select("*")
        query = query.eq("board_id", board["id"]).eq("is_active", True)
        
        # Order by is_pinned first (desc), then created_at (desc), then id (desc) for consistency
        # Use raw SQL ordering to ensure proper multi-column sort
        query = query.order("is_pinned.desc.nullslast,created_at.desc.nullslast,id.desc.nullslast")
        
        # Apply pagination
        query = query.limit(per_page)
        if offset > 0:
            query = query.offset(offset)
        
        response = query.execute()
        posts = response.data
        
        # Get total count
        count_result = db.select(
            "posts",
            filters={"board_id": board["id"], "is_active": True},
            count=True
        )
        total_count = count_result[0]["count"] if count_result else 0
    
    # Enrich posts with author info and comment count
    for post in posts:
        # Get author
        if post.get("user_id"):
            authors = db.select("users", filters={"id": post["user_id"]})
            if authors:
                post["author_name"] = authors[0].get("username", "익명")
            else:
                post["author_name"] = "익명"
        else:
            post["author_name"] = "익명"
        
        # Get comment count
        comments = db.select("comments", filters={"post_id": post["id"], "is_active": True}, count=True)
        post["comment_count"] = comments[0]["count"] if comments else 0
    
    # Calculate total pages
    total_pages = (total_count + per_page - 1) // per_page if total_count > 0 else 1
    
    # Create page range for pagination
    page_range = list(range(1, total_pages + 1))
    
    # Render the partial template
    return templates.TemplateResponse(
        "partials/board_posts.html",
        {
            "request": request,
            "board": board,
            "posts": posts,
            "can_write": can_write,
            "page": page,
            "total_pages": total_pages,
            "page_range": page_range,
            "search_query": q,
            "search_type": search_type
        }
    )


def create_initial_boards():
    """Create initial boards if they don't exist"""
    initial_boards = [
        {
            "name": "공지사항",
            "slug": "notice",
            "description": "중요한 공지사항을 게시하는 게시판입니다.",
            "can_read": "all",  # 모든 사용자가 읽을 수 있음
            "can_write": "admin",
            "display_order": 0
        },
        {
            "name": "뉴스레터",
            "slug": "newsletter",
            "description": "AICOM 뉴스레터를 모아놓은 게시판입니다.",
            "can_read": "all",  # 모든 사용자가 읽을 수 있음
            "can_write": "admin",
            "display_order": 1
        }
    ]
    
    for board_data in initial_boards:
        try:
            # Check if board already exists
            existing = db.select("boards", filters={"slug": board_data["slug"]})
            if not existing:
                # Create board
                db.insert("boards", board_data)
                print(f"Created initial board: {board_data['name']}")
            else:
                print(f"Board already exists: {board_data['name']}")
        except Exception as e:
            print(f"Error creating board {board_data['name']}: {e}")