import os
import secrets
from collections import OrderedDict
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort
)
from werkzeug.security import check_password_hash

from db import get_db, init_db


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("admin"):
            return redirect(url_for("admin_login"))
        return f(*args, **kwargs)
    return decorated


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE") == "1"

    # --- Publiek ---

    @app.route("/")
    def shop():
        db = get_db()
        rows = db.execute("SELECT * FROM pod ORDER BY categorie, naam").fetchall()
        db.close()
        per_categorie = OrderedDict()
        for r in rows:
            per_categorie.setdefault(r["categorie"], []).append(r)
        return render_template("shop.html", per_categorie=per_categorie)

    @app.route("/claim", methods=["POST"])
    def claim():
        pod_id = request.form.get("pod_id", type=int)
        naam = (request.form.get("bezoeker_naam") or "").strip()
        if not pod_id or not naam:
            flash("Vul je naam in om een pod te kiezen.", "fout")
            return redirect(url_for("shop"))
        db = get_db()
        try:
            pod = db.execute("SELECT * FROM pod WHERE id = ?", (pod_id,)).fetchone()
            if not pod:
                abort(404)
            if pod["stock"] < 1:
                flash(f"{pod['naam']} is helaas uitverkocht.", "fout")
                return redirect(url_for("shop"))
            db.execute(
                "INSERT INTO claim (pod_id, bezoeker_naam) VALUES (?, ?)",
                (pod_id, naam),
            )
            db.execute("UPDATE pod SET stock = stock - 1 WHERE id = ?", (pod_id,))
            db.commit()
        finally:
            db.close()
        return render_template("claim_done.html", pod=pod, naam=naam)

    register_admin_routes(app)
    return app


def register_admin_routes(app):
    @app.route("/admin/login", methods=["GET", "POST"])
    def admin_login():
        if request.method == "POST":
            db = get_db()
            row = db.execute(
                "SELECT waarde FROM setting WHERE sleutel = 'admin_wachtwoord_hash'"
            ).fetchone()
            db.close()
            wachtwoord = request.form.get("wachtwoord", "")
            if row and check_password_hash(row["waarde"], wachtwoord):
                session["admin"] = True
                return redirect(url_for("admin_stock"))
            return render_template("admin_login.html", fout="Verkeerd wachtwoord")
        if session.get("admin"):
            return redirect(url_for("admin_stock"))
        return render_template("admin_login.html", fout=None)

    @app.route("/admin/logout", methods=["POST"])
    def admin_logout():
        session.clear()
        return redirect(url_for("shop"))

    @app.route("/admin")
    @login_required
    def admin_stock():
        db = get_db()
        pods = db.execute("SELECT * FROM pod ORDER BY categorie, naam").fetchall()
        db.close()
        return render_template("admin_stock.html", pods=pods)

    @app.route("/admin/stock", methods=["POST"])
    @login_required
    def admin_stock_update():
        pod_id = request.form.get("pod_id", type=int)
        stock = request.form.get("stock", type=int)
        if pod_id is not None and stock is not None and stock >= 0:
            db = get_db()
            db.execute("UPDATE pod SET stock = ? WHERE id = ?", (stock, pod_id))
            db.commit()
            db.close()
            flash("Voorraad bijgewerkt.", "ok")
        return redirect(url_for("admin_stock"))

    @app.route("/admin/verkopen")
    @login_required
    def admin_sales():
        db = get_db()
        claims = db.execute(
            """SELECT claim.bezoeker_naam, claim.tijdstip,
                      pod.naam AS pod_naam, pod.categorie, pod.image_bestand
               FROM claim JOIN pod ON pod.id = claim.pod_id
               ORDER BY claim.tijdstip DESC"""
        ).fetchall()
        db.close()
        return render_template("admin_sales.html", claims=claims)


# WSGI-entrypoint
app = create_app()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=int(os.environ.get("PORT", 8500)))
