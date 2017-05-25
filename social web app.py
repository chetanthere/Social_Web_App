from flask import Flask, request, render_template, session
from pymongo import MongoClient
from gridfs import GridFS
import base64
import os
import sys
import datetime
import ast
from bson.objectid import ObjectId
import gridfs

app = Flask(__name__)
app.secret_key="chetan"

def cf():    
    client = MongoClient('mongodb:client')
    db = client.mdb5
    db.authenticate('myroot','mypawword'
    return db


@app.route('/', methods=['POST', 'GET'])
def index():
    print("m in index")
    return render_template('login.html')


@app.route('/register', methods=['POST','GET'])
def register():   
    mydb = cf()

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        groupname = request.form['groupname']
        cpassword = request.form['cpassword']

        # chk for password match
        if (password != cpassword) :
            register_result = "password is not confirmed correctly"
            return render_template('register.html', register_result=register_result)

        #chk max limit per grp
        cursor = mydb.register.find({"groupname":groupname})
        if (cursor.count() >= 4):
            register_result = "more than 4 users"
            return render_template('register.html', register_result=register_result)

        flag = 0
        cursor = mydb.register.find({"username": username})
        for document in cursor:
            gd = document['groupname']
            if gd == groupname:
                flag = 1
                break

        if flag == 1:
            register_result = "user is alredy in that grp"
            return render_template('register.html', register_result=register_result)

        if (cursor.count() >= 1):
            register_result = "users already there"
            return render_template('register.html', register_result=register_result)

        myrecord = {
            "username": username,
            "password": password,
            "groupname": groupname
        }

        record_id = mydb.register.insert(myrecord)      
        return render_template('login.html')
    else:
        return render_template('register.html')



@app.route('/login', methods=['POST'])
def login():
    t1 = datetime.datetime.now()   
    mydb = cf()
    login_result = ""

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        susername = str(username)       
        session["username"] = username

        t3 = datetime.datetime.now()
        cursor = mydb.register.find({"username": susername})
        t4 = datetime.datetime.now()
        print('cursor', cursor.count())
        mflag = 0
        if (cursor.count() == 0):
            mflag = 0
            print("nthng found")
            return render_template('register.html')
        else:
            for document in cursor:
                mpass = document["password"]
                if mpass == password:
                    mflag = 1
                    break
                else:
                    mflag = 0
        t2 = datetime.datetime.now()
        pt = t2 - t1
        dt = t4 - t3

        if (mflag == 1):
            return render_template('view1.html')
        else:
            login_result = "wrong credentials"
            return render_template('login.html', login_result=login_result)
                    
    else:
        return render_template('login.html', login_result=login_result)



@app.route('/upload', methods=['POST','GET'])
def upload():
    size = 3000000
    txtsize = 50    
    mydb = cf()
    username = session["username"]
    print("m in upload")

    #take inputs
    file1 = request.files['filename1']
    subject = request.form['subject']
    priority = request.form['priority']

    fn = file1.filename
    sfn = str(fn)
    fn,ftp = sfn.split('.')
    
    # read in the txt/image.
    thedata = file1.read()
    if ftp == "txt":
        sthedata = thedata
        txt_size = 0
        for line in thedata:
            txt_size += len(line)
        print('txt_size', txt_size)
        if txt_size > txtsize:
            upload_result = "txt size is more"
            return render_template("upload.html", upload_result=upload_result)
    else:
        sthedata = "data:image/jpeg;base64," + base64.b64encode(thedata)
        photo_size = sys.getsizeof(thedata)
        print('photo_size',photo_size)
        if photo_size > size:
            upload_result = "img size is more"
            return render_template("upload.html",upload_result=upload_result)

    cursor = mydb.udata.find({"username": username})

    if(cursor.count() >= 5):
        upload_result = "count reach max limit"
        return render_template("upload.html",upload_result=upload_result)
   
    current_ts = datetime.datetime.now()
    #store into db
    myrecord = {

        "user_name": username,
        "user_data": sthedata,
        "subject": subject,
        "priority" : priority,
        "upload_ts" : current_ts,
        "file_type" : ftp
    }

    record_id = mydb.udata.insert(myrecord)

    return render_template('filter.html')


@app.route('/filter', methods=['POST','GET'])
def filter():
    t0 = datetime.datetime.now()   
    mydb = cf()
    username = session["username"]
    viewuser = (request.form['viewuser'])
    if(viewuser == u''):
        viewuser = str(username)
    
    imgencodeddl = []
    t1 = datetime.datetime.now()
    if viewuser == "all":
        cursor = mydb.udata.find()
    else:
        cursor = mydb.udata.find({"user_name": viewuser})
    t2 = datetime.datetime.now()
    dt =  t2 - t1
    print('cursor count', cursor.count())
    t3 = datetime.datetime.now()
    for document in cursor:
        id  = document["_id"]
        user_name = document["user_name"]
        user_data = document["user_data"]
        subject = document["subject"]
        priority = document["priority"]
        upload_ts = document["upload_ts"]
        file_type = document["file_type"]
                    
        img = user_data
        imgencoded = img
        imgencodeddl.append({str(imgencoded): [str(id),str(user_name),str(subject),str(priority),str(upload_ts),str(file_type)]})
    t4 = datetime.datetime.now()
    dr =  t4 - t3
    tt = t4 - t0
    return render_template('view.html', imgencodeddl=imgencodeddl, dt=dt, dr=dr, tt=tt)


@app.route('/sort', methods=['POST','GET'])
def sort():   
    mydb = cf()
    username = session["username"]    
    sortc = request.form['sortc']    
    sorttype = str(request.form['sorttype'])
    sorttypei = int(sorttype)    
    ssortc = str(sortc)
    sss = "'" +ssortc +"'"
       
    imgencodeddl = []    
    t1 = datetime.datetime.now()

    if (sorttypei == 1):
        cursor = mydb.udata.find({"user_name" : username}).sort([(ssortc, 1)])
    else:
        cursor = mydb.udata.find({"user_name": username}).sort([(ssortc, -1)])
    
    t2 = datetime.datetime.now()
    dt = t2 - t1
    print('cursor', cursor.count())
    t3 = datetime.datetime.now()
    for document in cursor:
        id = document["_id"]
        user_name = document["user_name"]
        user_data = document["user_data"]
        subject = document["subject"]
        priority = document["priority"]
        upload_ts = document["upload_ts"]
        file_type = document["file_type"]
        
        img = user_data
        imgencoded = img   

        imgencodeddl.append(
            {str(imgencoded): [str(id), str(user_name), str(subject), str(priority), str(upload_ts), str(file_type)]})

    return render_template('view.html', imgencodeddl=imgencodeddl)


@app.route('/delete', methods=['POST','GET'])
def delete():
    mydb = cf()
    username = session["username"]
    susername = str(username)
    rid = request.form['rid']       
    mydb.udata.delete_one({'_id': ObjectId(rid)})
    return render_template("filter.html")


@app.route('/search', methods=['POST','GET'])
def search():
    mydb = cf()
    username = session["username"]
    search = request.form['search']
    searchc = request.form['searchc']
    searcho = request.form['searcho']
    ssearchc = str(searchc)
    ssearch = str(search)
    sss = "^" +ssearch
   
    if ssearchc == "upload_ts":
        hr = int(search)
        print(hr)
        print(datetime.datetime.now())
        at = datetime.datetime.now() + datetime.timedelta(hours=hr)       
        ssearch = at
    t1 = datetime.datetime.now()    
    if searcho == "eq":        
        cursor = mydb.udata.find({"user_name": username, ssearchc: {'$regex': search}})
    elif searcho == "neq":
        cursor = mydb.udata.find({"user_name": username, ssearchc: {'$not': ssearch}})
    elif searcho == "lt":
        cursor = mydb.udata.find({"user_name": username, ssearchc: {'$lt': ssearch}})
    elif searcho == "gt":
       cursor = mydb.udata.find({"user_name": username, ssearchc: {'$gt': ssearch}})
    elif searcho == "lte":
       cursor = mydb.udata.find({"user_name": username, ssearchc: {'$lte': ssearch}})
    elif searcho == "gte":
        cursor = mydb.udata.find({"user_name": username, ssearchc: {'$gte': ssearch}})
    else:
        ssearchs,ssearche = ssearch.split('-')
        ssearchss = str(ssearchs)
        ssearches = str(ssearche)       
        cursor = mydb.udata.find({"user_name": username, ssearchc: {'$gte': ssearchss,'$lte': ssearches}})
    t2 = datetime.datetime.now()
    print("cursor.count()",cursor.count())

    imgencodeddl = []
    for document in cursor:
        id = document["_id"]
        user_name = document["user_name"]
        user_data = document["user_data"]
        subject = document["subject"]
        priority = document["priority"]
        upload_ts = document["upload_ts"]
        file_type = document["file_type"]

        img = user_data
        imgencoded = img

        imgencodeddl.append({str(imgencoded): [str(id), str(user_name), str(subject), str(priority), str(upload_ts), str(file_type)]})

    return render_template('view.html', imgencodeddl=imgencodeddl)

                    
@app.route('/dele', methods=['POST','GET'])
def dele():
    mydb = cf()
    username = session["username"]   
    dele = request.form['dele']
    delec = request.form['delec']
    deleo = request.form['deleo']
    sdelec = str(delec)
    sdele = str(dele)
    sss = "^" +sdele
    
    dele1 = request.form['dele1']
    delec1 = request.form['delec1']
    deleo1 = request.form['deleo1']
    sdelec1 = str(delec1)
    sdele1 = str(dele1)
    sss1 = "^" + sdele1
   
    if delec == "upload_ts":
        hr = int(search)
        print(hr)
        print(datetime.datetime.now())
        at = datetime.datetime.now() + datetime.timedelta(minutes=hr)
        print ("at", at)
        sdele = at

    t1 = datetime.datetime.now()   
    if deleo == "eq2":
        mydb.udata.remove({"user_name" : username,sdelec: {'$eq': sdele}})
    elif deleo == "neq":
        mydb.udata.remove({"user_name": username, sdelec: {'$not': sdele}})
    elif ((deleo == "eq") and (deleo1 == "lt")):
        print("m here")
        mydb.udata.remove({"user_name": username, sdelec: {'$eq': sdele}, sdelec1: {'$lt': sdele1}})
    elif deleo == "gt":
        mydb.udata.remove({"user_name": username, sdelec: {'$gt': sdele}})
    elif deleo == "lte":
        print("in lte")
        mydb.udata.remove({"user_name": username, sdelec: {'$lte': sdele}})
    elif deleo == "gte":
        mydb.udata.remove({"user_name": username, sdelec: {'$gte': sdele}})
    else:
        sdeles,sdelee = sdele.split('-')
        sdeless = str(sdeles)
        sdelees = str(sdelee)
        print("sdeless",sdeless)
        print("sdelees",sdelees)
        cursor = mydb.udata.remove({"user_name": username, sdelec: {'$gte': sdeless,'$lte': sdelees}})
    t2 = datetime.datetime.now()
    
    cursor = mydb.udata.find({"user_name": username})
    imgencodeddl = []
    for document in cursor:
        id = document["_id"]
        user_name = document["user_name"]
        user_data = document["user_data"]
        subject = document["subject"]
        priority = document["priority"]
        upload_ts = document["upload_ts"]
        file_type = document["file_type"]

        img = user_data
        imgencoded = img

        imgencodeddl.append({str(imgencoded): [str(id), str(user_name), str(subject), str(priority), str(upload_ts), str(file_type)]})

    return render_template('view.html', imgencodeddl=imgencodeddl)


@app.route('/final5', methods=['POST','GET'])
def final5():   
    mydb = cf()
    username = session["username"]    
    newgroup = request.form['newgroup']
    fs = GridFS(mydb)    
    return render_template("login.html")
                    

@app.route('/final6', methods=['POST','GET'])
def final6():    
    mydb = cf()
    username = session["username"]
    susername = str(username)    
    search = request.form['search']
    ssearch = str(search)
    sss = "'^" +search +"'"   

    mydb.comment.remove({"comment": {'$regex':'^group2'}})
    return render_template("login.html")
    

if __name__ == '__main__':    
    app.run()
