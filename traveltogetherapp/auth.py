from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, Participation, TripProposal, ProposalStatus
from .forms import RegisterForm, LoginForm, ProfileForm
import re

auth_bp = Blueprint("auth", __name__)

# Enkel epost-sjekk (bypass av email_validator)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        email = (form.email.data or "").strip()
        password = form.password.data

        if not EMAIL_RE.match(email):
            flash("Ugyldig e-postadresse.", "danger")
            return render_template("auth_register.html", form=form)

        if User.query.filter_by(email=email).first():
            flash("Email already registered.", "warning")
            return render_template("auth_register.html", form=form)

        # Bruk Werkzeug sin default: pbkdf2:sha256
        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password, description="")
        db.session.add(user)
        db.session.commit()
        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth_register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        email = (form.email.data or "").strip()
        user = User.query.filter_by(email=email).first()
        if not user or not check_password_hash(user.password, form.password.data):
            flash("Invalid email or password.", "danger")
            return render_template("auth_login.html", form=form)
        login_user(user)
        return redirect(url_for("proposals.list_proposals"))
    return render_template("auth_login.html", form=form)


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))


# --- Manglende endepunkt: profilvisning ---
@auth_bp.route("/profile/<int:user_id>")
@login_required
def profile_view(user_id):
    user = User.query.get_or_404(user_id)
    # Hent alle proposals denne brukeren deltar i
    parts = Participation.query.filter_by(user_id=user.id).all()
    proposals = [TripProposal.query.get(p.proposal_id) for p in parts]

    # Split active vs inactive
    active = [p for p in proposals if p and p.status in (ProposalStatus.open, ProposalStatus.closed_to_new_participants)]
    inactive = [p for p in proposals if p and p.status in (ProposalStatus.finalized, ProposalStatus.cancelled)]

    return render_template("profile_view.html", user=user, active_proposals=active, inactive_proposals=inactive)


# (valgfritt, men matcher templaten din)
@auth_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    form = ProfileForm(request.form if request.method == "POST" else None)
    if request.method == "POST" and form.validate():
        current_user.description = form.description.data or ""
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("auth.profile_view", user_id=current_user.id))
    # prefill når GET
    if request.method == "GET":
        if hasattr(form, "description"):
            form.description.data = current_user.description or ""
    return render_template("profile_edit.html", form=form)
