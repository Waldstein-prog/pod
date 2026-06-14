import os
import secrets
from collections import OrderedDict
from functools import wraps

from flask import (
    Flask, render_template, request, redirect, url_for, session, flash, abort, jsonify
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


def _is_live(db):
    row = db.execute(
        "SELECT waarde FROM setting WHERE sleutel = 'giveaway_live'"
    ).fetchone()
    return bool(row and row["waarde"] == "1")


def _set_setting(db, sleutel, waarde):
    db.execute(
        "INSERT INTO setting (sleutel, waarde) VALUES (?, ?) "
        "ON CONFLICT(sleutel) DO UPDATE SET waarde = excluded.waarde",
        (sleutel, waarde),
    )


# pod-rij met afgeleide tellingen: claimed = aantal actieve claims, remaining = vrij
PODS_QUERY = """
    SELECT pod.*,
           COALESCE((SELECT COUNT(*) FROM claim WHERE claim.pod_id = pod.id), 0) AS claimed,
           MAX(0, pod.stock - COALESCE(
               (SELECT COUNT(*) FROM claim WHERE claim.pod_id = pod.id), 0)) AS remaining
    FROM pod
    ORDER BY categorie, naam
"""


def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get("SECRET_KEY", secrets.token_hex(32))
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
    app.config["SESSION_COOKIE_SECURE"] = os.environ.get("SESSION_COOKIE_SECURE") == "1"

    @app.context_processor
    def inject_live():
        db = get_db()
        try:
            return {"giveaway_live": _is_live(db)}
        finally:
            db.close()

    # --- Publiek ---

    @app.route("/")
    def shop():
        db = get_db()
        rows = db.execute(PODS_QUERY).fetchall()
        db.close()
        per_categorie = OrderedDict()
        for r in rows:
            per_categorie.setdefault(r["categorie"], []).append(r)
        return render_template(
            "shop.html",
            per_categorie=per_categorie,
            entered=bool(session.get("twitch")),
            claimed=session.get("claimed"),
        )

    @app.route("/enter", methods=["POST"])
    def enter():
        db = get_db()
        live = _is_live(db)
        db.close()
        if not live:
            flash("The giveaway is not live right now.", "fout")
            return redirect(url_for("shop"))
        twitch = (request.form.get("bezoeker_naam") or "").strip()
        palia = (request.form.get("palia_naam") or "").strip()
        if not twitch or not palia:
            flash("Please fill in both your Twitch name and your Palia name.", "fout")
            return redirect(url_for("shop"))
        session["twitch"] = twitch
        session["palia"] = palia
        return redirect(url_for("shop"))

    @app.route("/claim", methods=["POST"])
    def claim():
        twitch = session.get("twitch")
        palia = session.get("palia")
        if not twitch:
            flash("Please enter your Twitch and Palia name first.", "fout")
            return redirect(url_for("shop"))
        db = get_db()
        try:
            if not _is_live(db):
                flash("The giveaway is not live.", "fout")
                return redirect(url_for("shop"))
            if session.get("claimed"):
                flash("You already claimed a pod.", "fout")
                return redirect(url_for("shop"))
            pod_id = request.form.get("pod_id", type=int)
            pod = db.execute("SELECT * FROM pod WHERE id = ?", (pod_id,)).fetchone()
            if not pod:
                abort(404)
            taken = db.execute(
                "SELECT COUNT(*) FROM claim WHERE pod_id = ?", (pod_id,)
            ).fetchone()[0]
            if taken >= pod["stock"]:
                flash(f"{pod['naam']} is already gone.", "fout")
                return redirect(url_for("shop"))
            db.execute(
                "INSERT INTO claim (pod_id, bezoeker_naam, palia_naam, status) "
                "VALUES (?, ?, ?, 'pending')",
                (pod_id, twitch, palia),
            )
            db.commit()
            session["claimed"] = pod_id
        finally:
            db.close()
        return render_template("claim_done.html", pod=pod, naam=twitch)

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
            return render_template("admin_login.html", fout="Wrong password")
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
        pods = db.execute(PODS_QUERY).fetchall()
        db.close()
        return render_template("admin_stock.html", pods=pods)

    @app.route("/admin/stock", methods=["POST"])
    @login_required
    def admin_stock_update():
        pod_id = request.form.get("pod_id", type=int)
        stock = request.form.get("stock", type=int)
        if pod_id is None or stock is None or stock < 0:
            return jsonify({"ok": False}), 400
        db = get_db()
        db.execute("UPDATE pod SET stock = ? WHERE id = ?", (stock, pod_id))
        db.commit()
        taken = db.execute(
            "SELECT COUNT(*) FROM claim WHERE pod_id = ?", (pod_id,)
        ).fetchone()[0]
        db.close()
        return jsonify({"ok": True, "remaining": max(0, stock - taken)})

    @app.route("/admin/live", methods=["POST"])
    @login_required
    def admin_live():
        db = get_db()
        _set_setting(db, "giveaway_live", "1")
        db.commit()
        db.close()
        flash("Giveaway is now LIVE.", "ok")
        return redirect(url_for("admin_stock"))

    @app.route("/admin/stop", methods=["POST"])
    @login_required
    def admin_stop():
        db = get_db()
        _set_setting(db, "giveaway_live", "0")
        db.commit()
        db.close()
        flash("Giveaway stopped.", "ok")
        return redirect(url_for("admin_stock"))

    @app.route("/admin/reset", methods=["POST"])
    @login_required
    def admin_reset():
        db = get_db()
        db.execute("DELETE FROM claim")
        db.execute("UPDATE pod SET stock = begin_stock")
        db.commit()
        db.close()
        flash("Claims cleared and quantities restored to the start values.", "ok")
        return redirect(url_for("admin_stock"))

    @app.route("/admin/save-start", methods=["POST"])
    @login_required
    def admin_save_start():
        db = get_db()
        db.execute("UPDATE pod SET begin_stock = stock")
        db.commit()
        db.close()
        flash("Current quantities saved as the start values.", "ok")
        return redirect(url_for("admin_stock"))

    @app.route("/admin/verkopen")
    @login_required
    def admin_sales():
        db = get_db()
        claims = db.execute(
            """SELECT claim.id, claim.bezoeker_naam, claim.palia_naam, claim.status,
                      claim.tijdstip, pod.naam AS pod_naam, pod.categorie, pod.image_bestand
               FROM claim JOIN pod ON pod.id = claim.pod_id
               ORDER BY claim.tijdstip DESC"""
        ).fetchall()
        db.close()
        return render_template("admin_sales.html", claims=claims)

    @app.route("/admin/claim/<int:cid>/confirm", methods=["POST"])
    @login_required
    def admin_claim_confirm(cid):
        db = get_db()
        db.execute("UPDATE claim SET status = 'confirmed' WHERE id = ?", (cid,))
        db.commit()
        db.close()
        flash("Claim confirmed.", "ok")
        return redirect(url_for("admin_sales"))

    @app.route("/admin/claim/<int:cid>/cancel", methods=["POST"])
    @login_required
    def admin_claim_cancel(cid):
        db = get_db()
        db.execute("DELETE FROM claim WHERE id = ?", (cid,))
        db.commit()
        db.close()
        flash("Claim cancelled — pod released.", "ok")
        return redirect(url_for("admin_sales"))


# WSGI-entrypoint
app = create_app()

if __name__ == "__main__":
    init_db()
    app.run(debug=True, port=int(os.environ.get("PORT", 8500)))
