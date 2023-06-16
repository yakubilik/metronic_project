import base64
import os
import threading
import time

from flask import (Flask, abort, jsonify, redirect, render_template, request,session,
                   send_file, url_for)
from flask_sqlalchemy import SQLAlchemy

from pdf_merger import merge_pdf_files
from flask import Flask, render_template, request, redirect
from flask import Flask, render_template, redirect, request
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_pymongo import PyMongo
from werkzeug.security import check_password_hash, generate_password_hash
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from bson import Binary, ObjectId


template_dir = os.path.abspath("./metronic_v8.0.37/html/demo1")
static_dir = os.path.abspath("./metronic_v8.0.37/html/demo1/dist/assets")


app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///inventory.db"
app.config["SECRET_KEY"] = "supersecretkey"
app.config["UPLOAD_FOLDER"] = "static/pdf_files"
#app.config["MONGO_URI"] = "mongodb+srv://yakupkeskin:<.,Kekem.,321>@cluster0.i3zpt7a.mongodb.net/?retryWrites=true&w=majority"
 # Replace with your MongoDB connection URI
#mongo = PyMongo(app)
#login_manager = LoginManager(app)

def connect_db():
    uri = "mongodb+srv://yakupkeskin:.,Kekem.,321@cluster0.i3zpt7a.mongodb.net/?retryWrites=true&w=majority"
    client = MongoClient(uri, server_api=ServerApi('1'))
    return client


db = SQLAlchemy(app)
#mon_client = connect_db()

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form.get("email")
        password = request.form.get("password")
        mon_client = connect_db()
        m_db = mon_client.get_database('tshirt_users')
        records = m_db.users
        user_data = records.find_one({"username": username})

        if user_data:
            if password == user_data["password"]:
                session["user"] = user_data["username"]
                return redirect(url_for('home'))
            else:
                print("Invalid username or password")
        mon_client.close()
    return render_template("/dist/authentication/layouts/basic/giriş-yap.html")

@app.route("/logout/",methods=["GET"])
def logout():
    if "user" in session:
        print("LOGOUT")
        session.pop("user", None)
    return redirect(url_for('login'))


# create inventory table
class Item(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), nullable=False)
    color = db.Column(db.String(80), nullable=False)
    size = db.Column(db.String(80), nullable=False)
    sex = db.Column(db.String(80), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    image = db.Column(db.LargeBinary, nullable=True)
    status = db.Column(db.String(20), nullable=False)

    def __repr__(self):
        return f"<Item {self.name}>"

class PageMode(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    mode = db.Column(db.String(10), nullable=False, default="Light")


@app.route("/change_page_mode")
def change_page_mode():
    mode_item = db.session.query(PageMode).first()
    print(mode_item.mode)
    if mode_item.mode == "light":
        mode_item.mode = "dark"
        db.session.commit()
    else:
        mode_item.mode = "light"
        db.session.commit()
    mode_item = db.session.query(PageMode).first()
    print("mode_item", mode_item.mode)
    return redirect(request.referrer)


# add new inventory item
@app.route("/inventory", methods=["GET"])
def inventory():
    if "user" in session:
        mon_client = connect_db()
        m_db = mon_client.get_database(session["user"])
        items_mon = m_db.items.find()
        items = list(items_mon)
        mode = db.session.query(PageMode).first().mode
        mon_client.close()
        return render_template("dist/apps/ecommerce/catalog/products.html", items=items, mode=mode)

    return redirect(url_for('login'))


@app.route("/inventory/add_product", methods=["GET", "POST"])
def inventory_add_item():
    if request.method == "POST":
        name = request.form["name"]
        color = request.form["color"]
        size = request.form["size"]
        sex = request.form["sex"]
        quantity = int(request.form["quantity"])
        status = request.form["status"]
        file = request.files["image"]
        image_data = base64.b64encode(file.read())

        mon_client = connect_db()
        m_db = mon_client.get_database(session["user"])
        item = m_db.items.find_one({"color": color, "size": size, "sex": sex})
        if item:
            item["quantity"] += int(quantity)
            m_db.items.update_one({"_id": item["_id"]}, {"$set": {"quantity": item["quantity"]}})
            alert = "There is already an item with this quantities in the database! Please edit that item!"
            return redirect(url_for('.inventory_add_item', alert=alert, alert_type="failed"))

        else:
            items_mon = m_db.items.find()
            id = 1 + len(list(items_mon))
            new_item = {
                "id":id,
                "name":name,
                "color":color,
                "size":size,
                "sex":sex,
                "quantity":quantity,
                "image":image_data,
                "status":status,
            }
            res = m_db.items.insert_one(new_item)
            #db.session.add(new_item)
            #db.session.commit()
            if res:
                alert = "Item Successfully Added!"
                return redirect(url_for('.inventory_add_item', alert=alert, alert_type="success"))
            else:
                alert = "Database Error! Please Inform IT Team!"
                return redirect(url_for('.inventory_add_item', alert=alert, alert_type="failed"))


    if "alert" in request.args:
        alert = request.args["alert"]
        alert_type = request.args["alert_type"]
    else:
        alert = ''
        alert_type=''
    mode = db.session.query(PageMode).first().mode
    return render_template("dist/apps/ecommerce/catalog/add-product.html", alert=alert, alert_type=alert_type, mode=mode)


# view specific inventory item by ID
@app.route("/inventory/edit_item/", methods=["GET", "POST"])
def edit_item():
    mon_client = connect_db()
    if request.method == "GET":
        item_id = int(request.args["id"])
        #item = Item.query.get(item_id)
        m_db = mon_client.get_database(session["user"])
        item = m_db.items.find_one({"id": item_id})

        if item:
            mode = db.session.query(PageMode).first().mode
            return render_template(
                "dist/apps/ecommerce/catalog/edit-product.html", item=item, mode=mode)
        else:
            abort(404)
    else:
        id = int(request.form["id"])
        m_db = mon_client.get_database(session["user"])
        item = m_db.items.find_one({"id": id})
        #item = Item.query.get(id)
        item["name"] = request.form["name"]
        item["color"] = request.form["color"]
        item["size"] = request.form["size"]
        item["sex"] = request.form["sex"]
        item["quantity"] = int(request.form["quantity"])
        item["status"] = request.form["status"]
        if "image" in request.form.keys():
            item["image"] = request.form["image"]
        m_db.items.update_one({"id": item["id"]}, {"$set": item})
        db.session.commit()
        mon_client.close()
        return redirect("/inventory")


# update inventory item by ID
@app.route("/inventory/update", methods=["POST"])
def update_item():
    item_id = request.json["id"]
    item = Item.query.get(item_id)
    print(request.json)
    if not item:
        abort(404)
    if not request.json:
        abort(400)
    if "name" in request.json:
        item.name = request.json["name"]
    if "color" in request.json:
        item.color = request.json["color"]
    if "size" in request.json:
        item.size = request.json["size"]
    if "sex" in request.json:
        item.sex = request.json["sex"]
    if "quantity" in request.json:
        item.quantity = request.json["quantity"]
    if "status" in request.json["status"]:
        item.status = request.json["status"]
    db.session.commit()
    return jsonify({f"item {item_id}": "Successfully Updated!"})


# delete inventory item by ID
@app.route("/inventory/delete/", methods=["GET"])
def delete_item():
    item_id = int(request.args["id"])
    #item = Item.query.get(item_id)

    mon_client = connect_db()
    m_db = mon_client.get_database(session["user"])
    item = m_db.items.find_one({"id": item_id})
    m_db.items.delete_one({"id": item_id})
    mon_client.close()

    if not item:
        abort(404)
    return redirect("/inventory")


@app.route("/inventory/decrease", methods=["POST"])
def decrease_quantity():
    item_id = request.form["item_id"]
    item = Item.query.get(item_id)
    if not item:
        abort(404)
    if not request.form or "quantity" not in request.form:
        abort(400)
    if item.quantity - int(request.form["quantity"]) < 0:
        abort(400)
    item.quantity -= int(request.form["quantity"])
    db.session.commit()
    return jsonify({"item": item.id})


@app.route("/", methods=["GET"])
def home():
    if "user" in session:
        mode = db.session.query(PageMode).first().mode

        return render_template("dist/dashboards/ecommerce.html", mode=mode)

    return redirect(url_for('login'))


@app.route("/update", methods=["POST"])
def update():

    req_data = request.json
    print(req_data)


def get_file_list(folder):
    file_list = []
    for file in os.listdir(folder):
        size = round(os.stat(f"{folder}/{file}").st_size * 0.001, 3)
        creation_time = time.ctime(os.stat(f"{folder}/{file}").st_mtime)
        sp_txt = creation_time.split(" ")
        creation_time = (
            sp_txt[2]
            + " "
            + sp_txt[1]
            + " "
            + sp_txt[0]
            + " "
            + sp_txt[3]
            + " "
            + sp_txt[3]
        )
        file_dict = {"file_name": file, "size": size, "creation_time": creation_time}
        file_list.append(file_dict.copy())

    return file_list


@app.route("/folders/", methods=["GET"])
def folders():
    if "user" in session:
        mode = db.session.query(PageMode).first().mode
        if "folder" in request.args:
            folder = request.args["folder"]
            file_list = get_file_list(folder)
            return render_template(
                "dist/apps/file-manager/files.html", file_list=file_list, folder=folder, mode=mode)
        try:
            alert = request.args["alert"]
            alert_type = request.args["alert_type"]
        except:
            alert=""
            alert_type=""
        return render_template("dist/apps/file-manager/folders.html",alert=alert,alert_type=alert_type,mode=mode)

    return redirect(url_for('login'))


@app.route("/folders/upload", methods=["GET", "POST"])
def pdf():
    folder = request.form["folder"]
    f = request.files["file"]
    f.save(f"{folder}/{f.filename}")
    return ("success", 200)


@app.route("/files/download/")
def download_file():
    file = request.args["file"]
    folder = request.args["folder"]
    path = f"{folder}/{file}"  # specify the path of the file you want to download
    return send_file(path, as_attachment=True)


@app.route("/files/delete_file/", methods=["GET"])
def delete_file():
    file = request.args["file"]
    folder = request.args["folder"]
    os.remove(f"{folder}/{file}")
    return redirect(f"/folders/?folder={folder}")

@app.route("/clear_folder/")
def clear_folder():
    folder = request.args["folder"]
    for file in os.listdir(folder):
        os.remove(f"{folder}/{file}")
    return redirect(request.referrer)



import re
def get_file_list(folder):
    file_list = []
    for file in os.listdir(folder):
        size = round(os.stat(f"{folder}/{file}").st_size * 0.001, 3)
        creation_time = time.ctime(os.stat(f"{folder}/{file}").st_mtime)
        sp_txt = creation_time.split(" ")
        creation_time = (
            sp_txt[2]
            + " "
            + sp_txt[1]
            + " "
            + sp_txt[0]
            + " "
            + sp_txt[4]
            + " "
            + sp_txt[3]
        )
        file_dict = {"file_name": file, "size": size, "creation_time": creation_time}
        file_list.append(file_dict.copy())

    return file_list

threader = True
@app.route("/folders/merge_pdfs/")
def merge_pdfs():
    global threader
    '''
    def merge_files():
        global threader
        for item in range(len(os.listdir("orders"))):
            print("MERGİNG")
            merge_pdf_files(
                order="orders/" + os.listdir("orders")[item],
                track="ups/" + os.listdir("ups")[item],
                file_number=len(os.listdir("merged_files")),
            )
            print("MERGED")
        threader = True
    '''

    def merge_files():
            global threader
            orders = []
            ups = []
            counter = 0
            files = os.listdir("Orders-Ups")
            files.sort(key=lambda f: [int(s) if s.isdigit() else s for s in re.split(r'(\d+)', f)])
            for item in files:
                if counter < len(os.listdir("Orders-Ups"))/2:
                    ups.append(item)
                    counter += 1
                else:
                    orders.append(item)
            for counter in range(len(ups)):
                print("MERGİNG")
                try:
                    merge_pdf_files(
                        order="Orders-Ups/" + orders[counter],
                        track="Orders-Ups/" + ups[counter],
                        file_number=len(os.listdir("merged_files"))+1,
                    )
                    print("MERGED")
                except Exception as e:
                    if counter >= len(ups):
                        threader = True
            threader = True

    if threader:
        t = threading.Thread(target=merge_files)
        t.start()
        threader = False
    else:
        alert = "There is already a merging process running. Please try again later."
        #return render_template("dist/apps/file-manager/folders.html", alert=alert, alert_type="alert alert-dismissible bg-danger d-flex flex-column flex-sm-row w-100 p-5 mb-10")
        return redirect(url_for('.folders',alert=alert, alert_type="alert alert-dismissible bg-danger d-flex flex-column flex-sm-row w-100 p-5 mb-10"))
    print("Thread Started")
    alert = "Pdf file merging successfully started. This may take few seconds. Merged pdf files will saved to 'Merged' folder."
    #return render_template("dist/apps/file-manager/folders.html", alert=alert, alert_type="alert alert-dismissible bg-light-success border border-success border-3 d-flex flex-column flex-sm-row w-100 p-5 mb-10")
    return redirect(url_for('.folders', alert=alert, alert_type="alert alert-dismissible bg-light-success border border-success border-3 d-flex flex-column flex-sm-row w-100 p-5 mb-10"))


"""
@app.route("/billing",methods=['GET','POST'])
def billing():
    form = UploadFileForm()
    if form.validate_on_submit():
        files_filenames = []
        for file in form.data["file"]:
            file_filename = secure_filename(file.filename)
            file.save(os.path.join(os.path.abspath(os.path.dirname(__file__)), app.config['UPLOAD_FOLDER'],
                               secure_filename(file.filename)))  # Then save the file
            files_filenames.append(file_filename)
        flash("File has been uploaded.")
    return render_template('billing.html', form=form)
    def validate_file(form, file):
    for file in form.data["file"]:
        if file.content_type != "application/pdf":
            raise ValidationError("Please Select a Pdf File!")
            flash("File has been uploaded.")
            return render_template('billing.html', form=form)

class UploadFileForm(FlaskForm):
    file = MultipleFileField("File", validators=[InputRequired(),validate_file])
    submit = SubmitField("Upload File")
"""


@app.route("/billing", methods=["GET", "POST"])
def billing():
    if request.method == "POST":
        for f in request.files.getlist("file_name"):
            if f.content_type == "application/pdf":
                f.save(os.path.join(app.config["UPLOAD_FOLDER"], f.filename))
    return render_template("billing.html")



if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        new_item = PageMode(
            mode="light"
        )
        db.session.add(new_item)
        db.session.commit()
    app.run(debug=True, threaded=True, port=5005, host="0.0.0.0")