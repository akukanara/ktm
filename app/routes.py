from flask import Blueprint, render_template, request, redirect, url_for, jsonify, abort, send_file, Response, current_app, flash
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from botocore.exceptions import BotoCoreError, NoCredentialsError
import boto3
import uuid
import os
import socket
from .models import db, Client, User
from .email import send_verification_email

main = Blueprint("main", __name__)


def check_port_availability(port, exclude_client_id=None):
    clients = Client.query.all()
    for client in clients:
        if exclude_client_id and client.client_id == exclude_client_id:
            continue
        if client.frpc_config:
            for proxy in client.frpc_config:
                if proxy.get('enabled') and proxy.get('remotePort') == port:
                    return f"Port {port} already in use by client {client.client_id}"
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('', port))
    except OSError:
        return f"Port {port} is already in use by system"
    return None


@main.route("/")
@login_required
def dashboard():
    clients = Client.query.filter_by(user_id=current_user.id).all()
    total_clients = len(clients)
    total_tunnels = sum(len(c.frpc_config or []) for c in clients)

    return render_template("dashboard.html", clients=clients,
                           total_clients=total_clients,
                           total_tunnels=total_tunnels)


@main.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        file = request.files.get("photo")
        email = request.form.get("email")
        password = request.form.get("password")

        updated = False

        # --- FOTO PROFIL ---
        if file and file.filename:
            filename = secure_filename(file.filename)
            ext = os.path.splitext(filename)[1]
            new_filename = f"{uuid.uuid4().hex}{ext}"

            use_s3 = current_app.config.get("USE_S3_UPLOAD", False)

            try:
                if use_s3:
                    s3 = boto3.client(
                        "s3",
                        region_name=current_app.config["S3_REGION"],
                        aws_access_key_id=current_app.config["S3_KEY"],
                        aws_secret_access_key=current_app.config["S3_SECRET"],
                    )
                    bucket = current_app.config["S3_BUCKET"]
                    s3.upload_fileobj(
                        file,
                        bucket,
                        f"profile_photos/{new_filename}",
                        ExtraArgs={'ACL': 'public-read', 'ContentType': file.content_type}
                    )
                    photo_url = f"https://{bucket}.s3.{current_app.config['S3_REGION']}.amazonaws.com/profile_photos/{new_filename}"
                else:
                    folder = current_app.config.get("PROFILE_UPLOAD_FOLDER", "data/profile/photos")
                    os.makedirs(folder, exist_ok=True)
                    path = os.path.join(folder, new_filename)
                    file.save(path)
                    photo_url = url_for('main.profile_photo', filename=new_filename)

                current_user.profile_url = photo_url
                updated = True
                flash("✅ Profile photo updated!", "success")
            except (BotoCoreError, NoCredentialsError, Exception) as e:
                flash(f"❌ Upload failed: {str(e)}", "danger")

        # --- EMAIL ---
        if email and email != current_user.email:
            current_user.email = email
            current_user.email_verified = False
            current_user.email_token = uuid.uuid4().hex
            updated = True

            if current_app.config.get("ENABLE_EMAIL_VERIFICATION"):
                from .email import send_verification_email
                try:
                    send_verification_email(current_user)
                    flash("📧 Verification email sent. Please check your inbox.", "info")
                except Exception as e:
                    flash(f"❌ Failed to send verification email: {e}", "danger")

        # --- PASSWORD ---
        if password:
            current_user.set_password(password)
            updated = True

        if updated:
            db.session.commit()
            flash("✅ Profile updated successfully.", "success")
        else:
            flash("⚠️ No changes made.", "warning")

        return redirect(url_for("main.profile"))

    return render_template("profile.html", user=current_user, config=current_app.config)



@main.route("/profile_photos/<filename>")
def profile_photo(filename):
    folder = current_app.config.get("PROFILE_UPLOAD_FOLDER", "data/profile/photos")
    path = os.path.join(folder, filename)
    if not os.path.exists(path):
        abort(404)
    return send_file(path)


@main.route("/clients", methods=["GET", "POST"])
@login_required
def clients():
    if request.method == "POST":
        client_id = request.form.get("client_id")
        if not client_id:
            flash("❌ Client ID is required.", "danger")
            return redirect(url_for("main.clients"))

        existing = Client.query.filter_by(client_id=client_id).first()
        if existing:
            flash("❌ Client ID already exists.", "danger")
            return redirect(url_for("main.clients"))

        token = uuid.uuid4().hex
        client = Client(client_id=client_id, token=token, frpc_config={}, user_id=current_user.id)
        db.session.add(client)
        db.session.commit()
        flash("✅ Client added successfully.", "success")
        return redirect(url_for("main.clients"))

    if current_user.role == "admin":
        all_clients = Client.query.all()
    else:
        all_clients = Client.query.filter_by(user_id=current_user.id).all()

    return render_template("clients.html", clients=all_clients)



@main.route("/api/<client_id>/kana_frpc.json")
def get_frpc(client_id):
    token = request.headers.get("X-Auth-Token")
    client = Client.query.filter_by(client_id=client_id).first()

    if not client or client.token != token:
        abort(403)

    response = {
        "common": {
            "server_addr": "192.168.225.3",
            "server_port": current_app.config.get("FRPS_BIND_PORT", 7000),
            "token": current_app.config.get("FRPS_GLOBAL_TOKEN", "thisiskanaratunnel"),
            "protocol": "tcp",
            "connect_timeout": 10
        },
        "proxies": client.frpc_config
    }

    return jsonify(response)


@main.route("/script/<client_id>/<token>-installer.sh")
def generate_installer(client_id, token):
    client = Client.query.filter_by(client_id=client_id, token=token).first_or_404()
    base = request.host_url.rstrip("/")

    template_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "lib", "installer_template.sh"))
    with open(template_path, "r") as f:
        template = f.read()

    filled_script = template.replace("{CLIENT_ID}", client_id)\
                            .replace("{TOKEN}", token)\
                            .replace("{BASE}", base)

    return Response(filled_script, mimetype="text/x-shellscript")


@main.route("/client/<client_id>/<token>/ktmc.py")
def serve_ktmc_py(client_id, token):
    client = Client.query.filter_by(client_id=client_id, token=token).first()
    if not client:
        abort(403)

    path = os.path.join(os.path.dirname(__file__), "../lib/ktmc.py")
    return send_file(path, mimetype="text/x-python")


@main.route("/client/<client_id>/<token>/frpc")
def serve_frpc(client_id, token):
    client = Client.query.filter_by(client_id=client_id, token=token).first()
    if not client:
        abort(403)

    path = os.path.join(os.path.dirname(__file__), "../lib/bin/frp/frpc")
    return send_file(path, mimetype="application/octet-stream")


@main.route("/client/<client_id>/<token>/config.json")
def serve_config_json(client_id, token):
    client = Client.query.filter_by(client_id=client_id, token=token).first()
    if not client:
        abort(403)

    api_url = f"{request.host_url.rstrip('/')}/api/{client.client_id}/kana_frpc.json"
    cfg = {
        "client_id": client.client_id,
        "token": client.token,
        "api_url": api_url,
        "frpc_path": "./bin/frp/frpc",
        "frpc_config_file": "frpc.ini",
        "check_interval": 30
    }

    return jsonify(cfg)


@main.route("/clients/<client_id>/tunnels", methods=["GET", "POST"])
@login_required
def manage_tunnels(client_id):
    client = Client.query.filter_by(client_id=client_id).first_or_404()
    if current_user.role != "admin" and client.user_id != current_user.id:
        abort(403)

    if request.method == "POST":
        data = request.get_json()
        proxies = data.get('proxies', []) or []
        action = data.get('action', '')

        if action == 'validate':
            for proxy in proxies:
                if proxy.get('enabled'):
                    port = proxy.get('remotePort')
                    error = check_port_availability(port, exclude_client_id=client_id)
                    if error:
                        return jsonify({"error": error}), 400
            return jsonify({"message": "Port available"}), 200

        if 'proxies' in data:
            client.frpc_config = proxies
            db.session.commit()
            return jsonify({"message": "Tunnels saved"}), 200

        return jsonify({"error": "Invalid action"}), 400

    return render_template("tunnels.html", client=client, frpc_config=client.frpc_config)

@main.route("/clients/<client_id>/tunnels/add", methods=["POST"])
@login_required
def add_tunnel(client_id):
    client = Client.query.filter_by(client_id=client_id).first_or_404()
    if current_user.role != "admin" and client.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json()
    proxies = data.get('proxies', [])
    if not proxies:
        return jsonify({"error": "No proxy data"}), 400

    new = proxies[0]
    if new.get('enabled'):
        port = new.get('remotePort')
        error = check_port_availability(port)
        if error:
            return jsonify({"error": error}), 400

    client.frpc_config = (client.frpc_config or []) + [new]
    db.session.commit()
    return jsonify({"message": "Tunnel added"}), 200


@main.route("/clients/<client_id>/tunnels/edit", methods=["POST"])
@login_required
def edit_tunnel(client_id):
    client = Client.query.filter_by(client_id=client_id).first_or_404()
    if current_user.role != "admin" and client.user_id != current_user.id:
        return jsonify({"error": "forbidden"}), 403

    data = request.get_json()
    edited = data.get('proxy')
    index = data.get('index')

    if edited is None or index is None:
        return jsonify({"error": "Missing data"}), 400

    if edited.get('enabled'):
        port = edited.get('remotePort')
        error = check_port_availability(port, exclude_client_id=client_id)
        if error:
            return jsonify({"error": error}), 400

    if index < 0 or index >= len(client.frpc_config):
        return jsonify({"error": "Invalid index"}), 400

    client.frpc_config[index] = edited
    db.session.commit()
    return jsonify({"message": "Tunnel edited"}), 200


@main.route("/profile/update", methods=["POST"])
@login_required
def profile_update():
    email = request.form.get("email")
    password = request.form.get("password")

    updated = False

    if email and email != current_user.email:
        current_user.email = email
        current_user.email_verified = False
        current_user.email_token = uuid.uuid4().hex
        updated = True
        if current_app.config.get("ENABLE_EMAIL_VERIFICATION"):
            send_verification_email(current_user)  # ✅ cukup 1 argumen

    if password:
        current_user.set_password(password)
        updated = True

    if updated:
        db.session.commit()
        flash("✅ Profile updated successfully.", "success")
    else:
        flash("⚠️ No changes made.", "warning")

    return redirect(url_for("main.profile"))



@main.route("/verify_email/<token>")
def verify_email(token):
    user = User.query.filter_by(email_token=token).first()
    if not user:
        flash("Invalid or expired verification link.", "danger")
        return redirect(url_for("main.profile"))

    user.email_verified = True
    user.email_token = None
    db.session.commit()
    return redirect(url_for("main.verify_email_success"))



@main.route("/resend_verification", methods=["POST"])
@login_required
def resend_verification():
    if not current_user.email or current_user.email_verified:
        flash("Email sudah diverifikasi atau tidak tersedia.", "info")
        return redirect(url_for("main.profile"))

    from uuid import uuid4
    current_user.email_token = uuid4().hex
    db.session.commit()

    send_verification_email(current_user)  # ✅ cukup 1 argumen
    flash("📧 Link verifikasi telah dikirim ulang ke email kamu.", "success")
    return redirect(url_for("main.profile"))

@main.route("/verify_email/success")
def verify_email_success():
    return render_template("verify_success.html")


