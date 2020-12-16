from requests import Session

from fake_useragent import UserAgent


def set_up_session():
    ua = UserAgent()
    ua_string = ua.random
    session = Session()
    session.headers.update({'User-Agent': ua_string})
    return session