import datetime
import firebase_admin

from firebase_admin import db 
from firebase_admin import credentials , storage
from flask import Flask, render_template, request, flash , redirect , url_for , json , session
from google.auth.transport import requests
from google.cloud import storage
import google.oauth2.id_token

firebase_request_adapter = requests.Request()

app = Flask(__name__)


#Intialize Firebase database using firebase admin and service account json
cred = credentials.Certificate("projectalpha24-firebase-adminsdk-v7bkn-6294ec5f82.json")
firebase_admin.initialize_app(cred,{'databaseURL':"https://projectalpha24-default-rtdb.firebaseio.com"})


#reference to the users database
userDatabase = db.reference("Users")
#reference to the posts database
postDatabase = db.reference("Posts")

userImage = storage.Client()

#first page to load when app is launched
@app.route('/')
def login():
    return render_template('login.html')


#logout function
@app.route('/logout')
def logout():
    return render_template('login.html')

#get datetime in json format to store in firebase database
timeStamp = datetime.datetime.now()
formatTime = timeStamp.isoformat()
jsonTime = json.dumps(formatTime)

#function to redirect user to dashboard upon successful log in
@app.route("/" , methods = ["POST"])
def signin():
    #fetch user input from html form
    userId = request.form["UserId"]
    password = request.form["password"]
    #retrieve users data from database
    users = userDatabase.get()
    for key,value in users.items():
        if value["UserId"] == userId and value["password"] == password:
            session['username'] = value["UserName"]
            return redirect(url_for("forum" , usernname = session['username']))
    #validate user        
    flash("Id/password is wrong or User doesn't exist.Please Check your Id/password or register")
    return render_template("login.html")    

#function to register new users and add their data into firebase database
@app.route("/register", methods = ["GET","POST"])
def register():
    #manage post request
    if request.method == "POST":
        #fetch user input from html form
        userId = request.form["UserId"]
        password = request.form["password"]
        userName = request.form["UserName"]
        
        #retrieve users data from database
        users = userDatabase.get()
        for key,value in users.items():
            if value["UserId"] == userId:
                #validate userId
                flash("The Id already exists!") 
                return render_template("signup.html") 
            elif value["UserName"] == userName:
                #validate userName
                flash("The username already exists!") 
                return render_template("signup.html") 
        #push data into firebase database
        userDatabase.push().set({
        "UserId" : userId,
        "UserName" : userName,
        "password" : password
        })

        flash("Please Log in with your new credentials")
        return render_template("login.html")
    else:
        return render_template("signup.html")    

#render posts from firebase database after user posts
@app.route("/forum", methods = ["GET"])
def forum():
    forumPosts=[]
    #gets posts
    posts = postDatabase.order_by_value().limit_to_last(10).get()
    for key,value in posts.items():
        forumPosts.append(value)
    return render_template("forum.html", postss = forumPosts ,usernname = session['username'] )

#function to post message to firebase
@app.route("/postBlog", methods = ["POST"])
def postBlog():
    #fetch subject and message from html form
    Subject = request.form["subject"]
    message = request.form["message"]
    #post subject and message to database
    postDatabase.push().set({
        "UserName":session['username'],
        "Subject": Subject,
        "Message":message,
        "TimeStamp":jsonTime})
    return redirect(url_for('forum'))

#function to open user page
@app.route("/userPage", methods=["GET"])
def userPage():
    userPost=[]
    #get user posts
    userPosts = postDatabase.get()
    for key,value in userPosts.items():
        #get logged in user
        postDatabase.child(key)
        if session['username'] == value["UserName"]:
            userPost.append(value)
    return render_template("userpage.html" , postss = userPost , usernname = session['username'])
        
#function to change user password
@app.route("/updatePassword",methods=["POST"])
def updatePassword():
    #fetch old and new password from form
    oldPass = request.form["oldpassword"]
    newPass = request.form["newpassword"]
    #retrieve users data from database
    userPass = userDatabase.get()
    for key,value in userPass.items():
        #get specific user key to update password
        users = userDatabase.child(key)
        #validate password
        if value['password'] == oldPass and session['username'] == value["UserName"]:
            users.update({
                'password': newPass
            })
            return render_template("login.html")

    flash("Old password is incorrect")
    return redirect(url_for("userPage"))

#function to edit specific user posts on userpage
@app.route("/editPost", methods=["POST"])
def editPost():
    #fetch new user data
    newSubject = request.form["subject"]
    newMessage = request.form["message"]
    #get user posts
    userPosts = postDatabase.get()
    for key,value in userPosts.items():
      if(value["UserName"] == session['username']):  
            #get logged in user
            updatedPost = postDatabase.child(key)
            updatedPost.update({
                'Subject': newSubject,
                'Message': newMessage,
                'TimeStamp':jsonTime
            })
    return redirect(url_for('forum'))


app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

if __name__ == '__main__':

    app.run(host='127.0.0.1', port=5050, debug=True)
