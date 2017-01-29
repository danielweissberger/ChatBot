var ChatBot = {};
//CNN API KEY
//d0ae5510c62d45578cf7f992701ff98f

console.log(window.location.href.slice(0,-1));

//The server path will be used when sending the chat message to the server.
//todo replace with your server path if needed
ChatBot.SERVER_PATH = window.location.href.slice(0,-1);   //"http://localhost:7010";
ChatBot.DEFAULT_ANIMATION = "waiting";
//The animation timeout is used to cut the current running animations when a new animations starts
ChatBot.animationTimeout;
//Holds the speech synthesis configuration like language, pich and rate
ChatBot.speechConfig;
//Will be set to false automatically whan the browser does not support speech synthesis
//Or when the user clicks the mute button
ChatBot.speechEnabled = true;
ChatBot.twoWay = true;
//TODO: remove for production
ChatBot.debugMode = false;
ChatBot.userName = "";
ChatBot.partner = "";
//This function is called in the end of this file


ChatBot.start = function () {
    $(document).ready(function () {
        if(ChatBot.twoWay){
        ChatBot.userName = prompt("Enter a user name below for your chat:");
        $.get(ChatBot.SERVER_PATH+"/createUser/"+ChatBot.userName)
        }
        else{
            ChatBot.userName = "me"
        }
        ChatBot.debugPrint("Document is ready");
        ChatBot.bindErrorHandlers();
        ChatBot.initSpeechConfig();
        ChatBot.bindUserActions();
        ChatBot.write("You are in group mode, to talk to me (boto) click the button to the top left of the chat window or copy the url " + ChatBot.SERVER_PATH + " into another browser window to add a user", "boto");
        ChatBot.getMessages();
        });
};

//Handle Ajax Error, animation error and speech support
ChatBot.bindErrorHandlers = function () {
    //Handle ajax error, if the server is not found or experienced an error
    $(document).ajaxError(function (event, jqxhr, settings, thrownError) {
        ChatBot.handleServerError(thrownError);
    });

    //Making sure that we don't receive an animation that does not exist
    $("#emoji").error(function () {
        ChatBot.debugPrint("Failed to load animation: " + $("#emoji").attr("src"));
        ChatBot.setAnimation(ChatBot.DEFAULT_ANIMATION);
    });

    //Checking speech synthesis support
    if (typeof SpeechSynthesisUtterance == "undefined") {
        ChatBot.debugPrint("No speech synthesis support");
        ChatBot.speechEnabled = false;
        $("#mute-btn").hide();
    }
};

ChatBot.bindUserActions = function () {
    $("#twoway").on("click",function(){
        ChatBot.twoWay = !ChatBot.twoWay;
        if (ChatBot.twoWay){
            ChatBot.write("goodbye","boto")
            ChatBot.getMessages();
            $("#twoway").text("Group Mode");
           }
        else{
            ChatBot.write("Hello im here to help","boto")
            clearInterval(interval);
            $("#twoway").text("Bot Mode");
        }
        $.get(ChatBot.SERVER_PATH+"/setTwoWayMode/"+ChatBot.userName)

    });
    //Both the "Enter" key and clicking the "Send" button will send the user's message
    $('.chat-input').keypress(function (event) {
        if (event.keyCode == 13) {
            ChatBot.sendMessage();
        }
    });

    $(".chat-send").unbind("click").bind("click", function (e) {
        ChatBot.sendMessage();
    });

    //Mute button will toggle the speechEnabled indicator (when set to false the speak method will not be called)
    $("#mute-btn").unbind("click").bind("click", function (e) {
        $(this).toggleClass("on");
        ChatBot.speechEnabled = $(this).is(".on") ? false : true;
    });
};

//Initializeing HTML5 speech synthesis config 
ChatBot.initSpeechConfig = function () {
    if (ChatBot.speechEnabled) {
        ChatBot.speechConfig = new SpeechSynthesisUtterance();
        ChatBot.speechConfig.lang = 'en-US';
        ChatBot.speechConfig.rate = 1.6;
        ChatBot.speechConfig.pitch = 5;
        ChatBot.speechConfig.onend = function (event) {
            $("#speak-indicator").addClass("hidden");
        }
    }
};

var interval;

ChatBot.getMessages = function(){
        interval = setInterval(function(){

                $.get(ChatBot.SERVER_PATH+"/getUser/"+ChatBot.userName).done(function(msg){
                    user = JSON.parse(msg);
                    console.log(user);
                    for(var i=0;i<user["inbox"].length;i++){
                        ChatBot.write(user["inbox"][i]["msg"],user["inbox"][i]["user"]);
                    }
                });
                $.get(ChatBot.SERVER_PATH+"/clearInbox/"+ChatBot.userName);
                $.get(ChatBot.SERVER_PATH+"/getUsers").done(function(users){
                    users = JSON.parse(users);
                    for(var i =0;i<users.length;i++){
                        if(ChatBot.userName != users[i]["name"] && $("#"+users[i]["name"]).length ==0){
                            usertext = $("<span>").text(users[i]["name"]).attr("id",users[i]["name"]).css("display","block")
                            $("#users").append(usertext)
                        }

                    }
                });
            },300)

}

//The core function of the app, sends the user's line to the server and handling the response
ChatBot.sendMessage = function () {
    var sendBtn = $(".chat-send");
    //Do not allow sending a new message while another is being processed
    if (!sendBtn.is(".loading")) {
        var chatInput = $(".chat-input");
        //Only if the user entered a value
        if (chatInput.val()) {
            sendBtn.addClass("loading");


            ChatBot.write(chatInput.val(), ChatBot.userName)


            //Sending the user line to the server using the POST method
            var string = ChatBot.SERVER_PATH + "/chat/"+ChatBot.userName;
            console.log(string);
            debugger
            $.post(ChatBot.SERVER_PATH + "/chat/"+ChatBot.userName, {"msg": chatInput.val()}, function (result) {

                if (ChatBot.twoWay){
                    return result;
                }
                if (typeof result != "undefined" && "msg" in result) {

                    ChatBot.setAnimation(result.animation);
                    if (result.msg.constructor != Array){
                        ChatBot.write(result.msg, "boto");
                        }
                    else{
                        for(var i =0;i<result.msg.length;i++){
                            console.log(result.msg[i])
                            ChatBot.write(result.msg[i],"boto");
                        }
                     }
                } else {
                    //The server did not erred but we got an empty result (handling as error)
                    ChatBot.handleServerError("No result");
                }

            }, "json");
            chatInput.val("")
            sendBtn.removeClass("loading");
        }
    }
};

$.ajax("/test",{
    type: "POST",
    data: {"msg": "hello"},
    dataType: "json",
    contentType: "application/json"})
    .done(function (data) {
        console.log(data);
    });



ChatBot.write = function (message, sender, emoji) {
    console.log(message);
    //Only boto's messages should be heard
    if (sender == "boto" && ChatBot.speechEnabled) {
        ChatBot.speak(message);
    }
    var chatScreen = $(".chat-screen");
    sender = $("<span />").addClass("sender").addClass(sender).text(sender + ":");
    var msgContent = $("<span />").addClass("msg").text(message);
    var newLine = $("<div />").addClass("msg-row");
    newLine.append(sender).append(msgContent);
    chatScreen.append(newLine);
};

//Setting boto's current animation according to the server response
ChatBot.setAnimation = function (animation) {
    $("#emoji").attr("src", "./images/boto/" + animation + ".gif");
    //Cut the current running animations when a new animations starts
    clearTimeout(ChatBot.animationTimeout);
    //Each animation plays for 4.5 seconds
    ChatBot.animationTimeout = setTimeout(function () {
        $("#emoji").attr("src", "./images/boto/" + ChatBot.DEFAULT_ANIMATION + ".gif")
    }, 4500);
};

ChatBot.speak = function (msg) {
    $("#speak-indicator").removeClass("hidden");
    try {
        ChatBot.speechConfig.text = msg;
        speechSynthesis.speak(ChatBot.speechConfig);
    } catch (e) {
        $("#speak-indicator").addClass("hidden");
    }
};

ChatBot.handleServerError = function (errorThrown) {
    ChatBot.debugPrint("Server Error: " + errorThrown);
    var actualError = "";
    if (ChatBot.debugMode) {
        actualError = " ( " + errorThrown + " ) ";
    }
    ChatBot.write("Sorry, there seems to be an error on the server. Let's talk later. " + actualError, "boto");
    ChatBot.setAnimation("crying");
    $(".chat-send").removeClass("loading");
};

ChatBot.debugPrint = function (msg) {
    if (ChatBot.debugMode) {
        console.log("CHATBOT DEBUG: " + msg)
    }
};

ChatBot.start();