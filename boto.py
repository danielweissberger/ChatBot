"""
This is the template server side for ChatBot
"""

from bottle import route, run, template, static_file, request
import urllib
from urllib.parse import urlencode
import urllib.request
import json
import socket
from scraper import *

hostname = socket.gethostname()
IP = socket.gethostbyname(hostname)

two_way = {"userNames": []}
newsConvo = {"engaged": False}


# Call weather api to return local weather (based on users ip)

def check_for_weather(msg):
    print(msg)
    locate_ip_url = 'http://ipinfo.io/?token=$ec60ac6111cf6a'
    location = urllib.request.urlopen(locate_ip_url)
    location = json.loads(location.read().decode('utf-8'))

    url = 'https://api.darksky.net/forecast/aaebe17ba541b0d13aa0118879a8ffe7/+' \
          + location['loc']

    response = urllib.request.urlopen(url)
    result = json.loads(response.read().decode('utf-8'))

    if "weather" in msg.lower().split():
        print('im in here')
        return {"animation": "afraid", "msg": "The weather today is " + result['currently']['summary'] + ' with ' +
                str(result['currently']['humidity'])+'% humidity'}

    return None

#

def checkForGreeting(msg):

    greets = ["hello", "hi", "hey", "yo", "sup", "howdy"]
    if any(word in msg.lower().split() for word in greets):
        return {"animation": "inlove", "msg": "Hows it going dude?"}

    return None


def check_for_question(msg):

    questions = ["who", "what", "when", "where", "why", "how", "can", "may", "Is", "was", "will", "could", "might"]

    if any(word in msg.lower().split() for word in questions):

        return {"animation": "no", "msg": "That's a good question!"}

# This function checks for swears using neutrinoapi call to return json
def check_for_swear_words(msg):

    url = 'https://neutrinoapi.com/bad-word-filter'

    params = {
        'user-id': 'weissberger',
        'api-key': 'ibAgtqSxeuJxGtSue6Jw2gQqcS0MVaiuenzWk1aZAt70RYIp',
        'content': msg
    }

    encoded_params = urlencode(params).encode('utf8')
    response = urllib.request.urlopen(url, data=encoded_params)
    result = json.loads(response.read().decode('utf-8'))

    def get_boto_reply(result):

        if result['bad-words-total'] > 1:
            plural = "are"
            combiner = " and "
        else:
            plural = "is a"
            combiner = " "

        return {"animation": "crying", "msg": combiner.join(result['bad-words-list']) + " " + plural +
                " very bad word(s), watch your language it makes me cry"}

    if result["is-bad"]:
        if len(result["bad-words-list"]) >= 1:
            return get_boto_reply(result)

    else:
        return None


# This function checks for news using newsapi.org api call
def check_for_news(msg):

    if "news" in msg.split() and newsConvo["engaged"] is False:
        newsConvo["engaged"] = True
        return {"animation": "waiting", "msg": "What topic would you like to hear about"}

    elif newsConvo["engaged"] is True:
        news = json.loads(urllib.request.urlopen(
            "https://newsapi.org/v1/articles?source=cnn&sortBy=top&apiKey=d0ae5510c62d45578cf7f992701ff98f").read().decode(
            'utf-8'))
        try:
            topic_num = int(msg)-1
            newsConvo["engaged"] = False
            return {"animation": "ok", "msg": [news["articles"][topic_num]["description"] + " here is a link: ",
                                               news["articles"][topic_num]["url"]]}
        except:

            for article in news["articles"]:
                if msg.lower() in article["title"].lower().split():
                    newsConvo["engaged"] = False
                    return {"animation": "ok", "msg": [article["description"] + " here is a link: ", article["url"]]}
            topic_str = ""
            i = 1

            for article in news["articles"]:
                topic_str += str(i)+") " + article["title"] + " "
                i += 1

            return {"animation": "waiting","msg": 'Could not find that topic, please choose from list below: ' + topic_str}
    else:
        return None


def check_for_joke(msg):

    if "joke" in msg.lower().split():
        joke = json.loads(urllib.request.urlopen("http://api.icndb.com/jokes/random/").read().decode('utf-8'))
        return {"animation": "giggling", "msg": joke["value"]["joke"]}
    return None


# This function checks for different user requests.  It then calls various APIs or performs a google search if
# the user is asking a  question

def check_message(msg):

    joke = check_for_joke(msg)
    if joke:
        print(joke)
        return joke

    # weather = check_for_weather(msg)
    # if weather:
    #     print(weather)
    #     return weather

    swears = check_for_swear_words(msg)
    if swears:
        print(swears)
        return swears
    #
    greeting = checkForGreeting(msg)
    if greeting:
        print(greeting)
        return greeting

    news = check_for_news(msg)
    if news:
        print(news)
        return news

    # Check for a question, if true scrape google for a result (calling run_scraper from scraper.py)
    question = check_for_question(msg)
    if question:
        print(question)
        search_result = run_scraper(msg.replace('google', ''))
        return {"animation": "waiting", "msg": search_result[0]['url'] + '\n\n' + search_result[0]['description']}

    # Check for 'google' in message, if true scrape google for a result (calling run_scraper from scraper.py)
    if 'google' in msg:
        search_result = run_scraper(msg.replace('google', ''))
        return {"animation": "waiting", "msg": search_result[0]['url'] + '\n\n' + search_result[0]['description']}

    else:
        search_result = run_scraper(msg.replace('google', ''))
        return {"animation": "waiting", "msg": search_result[0]['url'] + '\n\n' + search_result[0]['description']}


@route('/', method='GET')
def index():
    return template("chatbot.html")


@route("/setTwoWayMode/<name>")
def set_two_way_mode(name):

    for user in two_way["userNames"]:
        if user["name"] == name:
            user["mode"] = not user["mode"]
            return


@route("/createUser/<username>")
def create_user(username):
    if username not in [user["name"] for user in two_way["userNames"]]:
        two_way["userNames"].append({"name":username, "mode": True, "inbox": []})


@route("/clearInbox/<username>")
def clear_inbox(username):
    for user in two_way["userNames"]:
        if user["name"] == username:
            user["inbox"] = []
            return None

# Returns a list of current users (for online screen)

@route("/getUsers")
def get_users():
    return json.dumps(two_way["userNames"])


@route("/getUser/<username>")
def get_user(username):
    for user in two_way["userNames"]:
        if user["name"] == username:
            return json.dumps(user)


# Calls the check_message function if group chat is disabled. If enabled it will check for other user messages and
# append them to the users inbox.
@route("/chat/<username>", method='POST')
def chat(username):
    for user in two_way["userNames"]:
        if user["name"] == username:
            break
    user_message = request.POST.get('msg')

    if user["mode"] is False:
        return json.dumps(check_message(user_message))
    else:

        for user in two_way["userNames"]:
            if user["name"] != username:
                user["inbox"].append({"user": username, "msg": user_message.replace("?", "")})

        return json.dumps({})


@route("/test", method='POST')
def chat():
    user_message = request.POST.get('msg')

    return json.dumps({"animation": "inlove", "msg": user_message})


@route('/js/<filename:re:.*\.js>', method='GET')
def javascripts(filename):
    return static_file(filename, root='js')

@route('/css/<filename:re:.*\.css>', method='GET')
def stylesheets(filename):
    return static_file(filename, root='css')


@route('/images/<filename:re:.*\.(jpg|png|gif|ico)>', method='GET')
def images(filename):
    return static_file(filename, root='images')

def main():
    run(host=IP, port=7555)

if __name__ == '__main__':
    main()
