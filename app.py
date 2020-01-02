import base64
import json
import re
import requests

from Crypto.Cipher import PKCS1_v1_5
from Crypto.PublicKey import RSA
from bs4 import BeautifulSoup

session = requests.Session()
session.headers.update({
    'User-agent':
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/79.0.3945.88 Safari/537.36'
})

INTERNET_HOME = 'https://id.its.ac.id/I/index.php'
INTERNET_LOGIN = 'https://integra.its.ac.id/index.php?n=internet&p='
LOGIN_POST = 'https://integra.its.ac.id/index.php'
INTEGRA_BASE = 'https://integra.its.ac.id/'

URL_PATTERN = re.compile(r"URL=([^'>]+)")


def process_login(login_url: str) -> bool:
    global session
    print('[PROCESS LOGIN] URL =', INTERNET_LOGIN)
    response = session.get(INTERNET_LOGIN)
    if response.status_code != 200:
        print('[GET LOGIN URL] Response', response.status_code)
        return False

    soup = BeautifulSoup(response.content, 'html.parser')
    pubkey = soup.find('input', {'id': 'pubkey'})
    if pubkey is None:
        print('[LOGIN FORM NOT FOUND]')
        return False

    pubkey = pubkey['value']
    rsa_pub_key = RSA.importKey(pubkey)
    cipher = PKCS1_v1_5.new(rsa_pub_key)

    login_data = json.load(open('login.json', 'r'))
    plain_text = login_data['userid'] + "|||" + login_data['password']
    encrypted = cipher.encrypt(plain_text.encode())
    encrypted = base64.encodebytes(encrypted).decode().strip()
    form_data = {'content': encrypted, 'p': '', 'n': 'internet'}
    response = session.post(LOGIN_POST, data=form_data)

    print('[LOGIN] Redirect 1')
    url_redirect = INTEGRA_BASE + URL_PATTERN.findall(response.text)[0]
    response = session.get(url_redirect)
    if response.status_code != 200:
        print('[LOGIN REDIRECT] Response', response.status_code)
        return False

    soup = BeautifulSoup(response.content, 'html.parser')
    form = soup.find('form')
    if form is None:
        print('[NOT FOUND] form redirect')
    action_url = form['action']
    inputs = form.findAll('input')

    form_data = {}
    for node in inputs[:-1]:
        name = node['name']
        value = node['value']
        form_data[name] = value

    response = session.post(action_url, data=form_data)

    print('[LOGIN] Redirect 2')
    soup = BeautifulSoup(response.content, 'html.parser')
    form = soup.find('form')
    if form is None:
        print('[NOT FOUND] form redirect')
    action_url = form['action']
    inputs = form.findAll('input')

    form_data = {}
    for node in inputs[:-1]:
        name = node['name']
        value = node['value']
        form_data[name] = value
    form_data['submit'] = 'redirect'

    response = session.post(action_url, data=form_data)
    print('[LOGIN] Redirect 3')
    soup = BeautifulSoup(response.content, 'html.parser')
    p = soup.find('p', {'class': 'lead mb-md-4'})
    if p is None:
        print('[NOT FOUND] p lanjutkan button')
        return False

    ahref = p.find('a')
    if ahref is None:
        print('[NOT FOUND] ahref lanjutkan button')
        return False

    if 'Lanjutkan' not in ahref.text:
        print(ahref)
        return False

    return True


def main():
    result = process_login(INTERNET_LOGIN)
    if result:
        print('LOGIN SUCCESS')
    else:
        print('LOGIN FAILED')


if __name__ == "__main__":
    main()