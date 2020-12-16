from typing import Any, Dict, List
from urllib.parse import urljoin

from reddit.util import set_up_session

url = "https://np.reddit.com"


def get_subreddits_from_response(js: Dict[str, Any], lang="en") -> List[Dict[str, Any]]:
    return [
        sub["data"]["url"]
        for sub in js["data"]["children"]
        if sub["data"].get("lang") == lang
    ]


def get_all_subreddits(lang="en") -> List[Dict[str, Any]]:
    """
    Retrieves all subreddits of a given language.
    :param lang:
    :return:
    """
    subs = []
    session = set_up_session()
    response = session.get(urljoin(url, "/reddits.json?limit=100"))
    subs.extend(get_subreddits_from_response(response.json(), lang))
    last_id = response.json()["data"]["after"]
    while True:
        response = session.get(urljoin(url, f"reddits.json?limit=100&after={last_id}"))
        if response.ok:
            js = response.json()
            subs.extend(get_subreddits_from_response(js, lang))
            print(subs)
            last_id = js["data"].get("after")
            if not last_id:
                break
    return subs


if __name__ == "__main__":
    subs = get_all_subreddits("de")
    print(subs)
    with open("subs-de.txt", "w") as file:
        file.write(",".join([s["displayName"] for s in subs]))
