import requests
from urllib import parse
from bs4 import BeautifulSoup as bs
from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
import base64

def get_auth_token(value):

    sIdno = value['uid']
    ssu_pwd = value['pw']

    common_header = {
        "referer": "https://smartid.ssu.ac.kr/Symtra_sso/smln.asp?apiReturnUrl=https%3A%2F%2Flms.ssu.ac.kr%2Fxn-sso%2Fgw-cb.php",
        "user-agent": ""
    }

    session = requests.Session()

    sToken_req_data = {
        "in_tp_bit": "0",
        "rqst_caus_cd": "03",
        "userid": sIdno,
        "pwd": ssu_pwd
    }

    # sToken 받아오기
    sToken_url = "https://smartid.ssu.ac.kr/Symtra_sso/smln_pcs.asp"
    res = session.post(sToken_url, headers = common_header, data = sToken_req_data)
    login_cookies = requests.utils.dict_from_cookiejar(session.cookies)
    sToken = login_cookies['sToken']

    # 쿠키 정보들 받아오기
    pass_token_url = f"https://lms.ssu.ac.kr/xn-sso/gw-cb.php?sToken={sToken}&sIdno={sIdno}"
    res = session.get(pass_token_url, headers = common_header)
    result = parse.urlparse(res.request.url)[4]

    # 암호화 된 canvas pwd 발급받기
    from_cc_url = f"https://canvas.ssu.ac.kr/learningx/login/from_cc?{result}"
    res = session.get(from_cc_url, headers=common_header)

    # pwd 파싱 및 복호화
    decrypt_pwd = decryption(res)

    canvas_data = {
        'utf8': "%E2%9C%93",
        'redirect_to_ssl': 1,
        'pseudonym_session[unique_id]': sIdno,
        'pseudonym_session[password]': decrypt_pwd,
        'pseudonym_session[remember_me]': 0
    }

    canvas_header = {
        "referer": from_cc_url,
        "user-agent": "",
    }

    # 복호화한 패스워드로 스마트캠퍼스 로그인하기
    canvas_url = f"https://canvas.ssu.ac.kr/login/canvas"
    res = session.post(canvas_url, headers = canvas_header, data = canvas_data)


    auth_token_header = {
        "referer": "https://lms.ssu.ac.kr/",
        "user-agent": "",
    }

    # 유저 정보 조회를 위한 토큰 발급
    token_url = f"https://canvas.ssu.ac.kr/learningx/dashboard?user_login={sIdno}&locale=ko"
    res = session.get(token_url, headers = auth_token_header)

    auth_token = res.headers['Set-Cookie'].split(";")[0][13:]
    return auth_token


def decryption(res):
    soup = bs(res.text, 'lxml')

    # key와 암호화 된 pwd 파싱하기
    elements = soup.select('script')
    element = list(elements[2].text.lstrip().split("\""))
    cryt = element[1]
    private = element[3].replace("-----BEGIN RSA PRIVATE KEY-----", "").replace("-----END RSA PRIVATE KEY-----", "")

    pem_prefix = '-----BEGIN RSA PRIVATE KEY-----\n'
    pem_suffix = '\n-----END RSA PRIVATE KEY-----'
    private = '{}{}{}'.format(pem_prefix, private, pem_suffix)

    # 발급받은 pw 복호화하기
    rsa_key = RSA.importKey(private)
    cipher = PKCS1_v1_5.new(rsa_key)

    raw_cyp = base64.b64decode(cryt)
    decrypt_pwd = cipher.decrypt(raw_cyp, None).decode()

    return decrypt_pwd

