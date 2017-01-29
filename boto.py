"""
This is the template server side for ChatBot
"""

from bottle import route, run, template, static_file, request
import json
import urllib.request
import socket

hostname = socket.gethostname()
IP = socket.gethostbyname(hostname)

twoWay = {"userNames":[]}
newsConvo = {"engaged":False}
from urllib.parse import urlencode


def checkForWeather(msg):
    if ("what" and "weather") in msg.lower().split():
        return {"animation":"afraid","msg":"Its freezing, you are in Tel Aviv!!"}
    return None

def checkForGreeting(msg):
    greets= ["hello","hi","hey","yo","sup","howdy"]
    if any(word in msg.lower().split() for word in greets):
        return {"animation": "inlove","msg":"Hows it going dude?"}
    return None

def checkForQuestion(msg):
    questions = ["what","when","where","why","how","can","may"]
    if any(word in msg.lower().split() for word in questions):
        return {"animation": "no","msg":"Thats a good question!"}

def checkForSwears(msg):
    swears = ["fuck","shit","ass","bitch","whore","hoe","cunt","motherfucker"]
    url = 'https://neutrinoapi.com/bad-word-filter'
    params = {
        'user-id': 'weissberger',
        'api-key': 'ibAgtqSxeuJxGtSue6Jw2gQqcS0MVaiuenzWk1aZAt70RYIp',
        'content': msg
    }

    encoded_params = urlencode(params).encode('utf8')
    response = urllib.request.urlopen(url, data=encoded_params)
    result = json.loads(response.read().decode('utf-8'))

    def getReturnString(result):
        if len(result)>1:
            plural = "are"
            combiner = " and "
        else:
            plural = "is a"
            combiner = " "
        return {"animation":"crying","msg":(combiner).join(result) +" "+ plural + " very bad, watch your language it makes me cry"}

    try:
        if result["is-bad"]:
            if len(result["bad-words-list"])>1:
                return getReturnString(result["bad-words-list"])

        return None
    except:
        detectedSwears = [word for word in msg.split() if word in swears]
        if len(detectedSwears)>1:
            return getReturnString(detectedSwears)
        else:
            return None

def checkForNews(msg):
    if "news" in msg.split() and newsConvo["engaged"]==False:
        newsConvo["engaged"] = True
        return {"animation": "waiting", "msg": "What topic would you like to hear about"}

    elif newsConvo["engaged"] == True:
        news = json.loads(urllib.request.urlopen(
            "https://newsapi.org/v1/articles?source=cnn&sortBy=top&apiKey=d0ae5510c62d45578cf7f992701ff98f").read().decode(
            'utf-8'))
        try:
            topicNum = int(msg)-1
            newsConvo["engaged"] = False
            return {"animation":"ok","msg":[news["articles"][topicNum]["description"] + " here is a link: ",  news["articles"][topicNum]["url"]]}
        except:
            for article in news["articles"]:
                if msg.lower() in article["title"].lower().split():
                    newsConvo["engaged"] = False
                    return {"animation":"ok","msg":[article["description"] + " here is a link: ", article["url"]]}
            topicsStr = "";
            i=1;
            for article in news["articles"]:
                topicsStr += str(i)+") " + article["title"] + " "
                i+=1;
            return {"animation":"waiting","msg":'Couldnt find that topic, please choose from list below: ' + topicsStr}
    else:
        return None


def checkForJoke(msg):
    if "joke" in msg.lower().split():
        joke = json.loads(urllib.request.urlopen("http://api.icndb.com/jokes/random/").read().decode('utf-8'))
        return {"animation":"giggling","msg":joke["value"]["joke"]}
    return None

def checkMessage(msg):
    weather = checkForWeather(msg)
    if weather:return weather

    swears = checkForSwears(msg)
    if swears:return swears

    greeting = checkForGreeting(msg)
    if greeting:return greeting

    news = checkForNews(msg)
    if news:return news

    joke = checkForJoke(msg)
    if joke:return joke

    question = checkForQuestion(msg)
    if question:return question

    else:
        return {"animation":"inlove","msg":"I didnt understand that, im a pretty dumb boto"}

@route('/', method='GET')
def index():
    return template("chatbot.html")


@route("/setTwoWayMode/<name>")
def setTwoWayMode(name):
    for user in twoWay["userNames"]:
        if user["name"]==name:
            user["mode"] = not user["mode"]
            return;

@route("/createUser/<username>")
def createUser(username):
    if username not in [user["name"] for user in twoWay["userNames"]]:
        twoWay["userNames"].append({"name":username,"mode":True,"inbox":[]})


@route("/clearInbox/<username>")
def clearInbox(username):
    for user in twoWay["userNames"]:
        if user["name"] == username:
            user["inbox"] = [];
            return;

@route("/getUsers")
def getUsers():
    return json.dumps(twoWay["userNames"])

@route("/getUser/<username>")
def getUser(username):
    for user in twoWay["userNames"]:
        if user["name"]==username:
            return json.dumps(user)

@route("/chat/<username>", method='POST')
def chat(username):
    for user in twoWay["userNames"]:
        if user["name"]==username:
            break
    user_message = request.POST.get('msg')
    if user["mode"]==False:
        return json.dumps(checkMessage(user_message))
    else:

        for user in twoWay["userNames"]:
            if user["name"]!= username:
                user["inbox"].append({"user":username ,"msg":user_message.replace("?","")})
        return json.dumps({})




@route("/test", method='POST')
def chat():
    user_message = request.POST.get('msg') #print this


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
    run(host=IP, port=7650)

if __name__ == '__main__':
    main()
