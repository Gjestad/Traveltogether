from flask import Blueprint, render_template, redirect, url_for, request, flash
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import login_user, logout_user, login_required, current_user
from .models import db, User, Participation, TripProposal, ProposalStatus
from .forms import RegisterForm, LoginForm, ProfileForm
import re

auth_bp = Blueprint("auth", __name__)

# Simple email check (bypassing email_validator)
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    form = RegisterForm(request.form)
    if request.method == "POST" and form.validate():
        email = form.email.data.strip()
        password = form.password.data

        if not EMAIL_RE.match(email):
            flash("Ugyldig e-postadresse.", "danger")
            return render_template("auth_register.html", form=form)

        query = db.select(User).where(User.email == email)
        user = db.session.execute(query).scalar_one_or_none()
        if user:
            flash("Email already registered.", "warning")
            return render_template("auth_register.html", form=form)

        hashed_password = generate_password_hash(password)
        user = User(email=email, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        
        login_user(user)
        flash("Registration successful! Please set your user name and profile.", "success")
        return redirect(url_for("auth.profile_edit"))
    return render_template("auth_register.html", form=form)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm(request.form)
    if request.method == "POST" and form.validate():
        email = form.email.data.strip()
        query = db.select(User).where(User.email == email)
        user = db.session.execute(query).scalar_one_or_none()
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
    user = db.session.get(User, user_id)
    if not user:
        flash("User not found.", "danger")
        return redirect(url_for("proposals.list_proposals"))
    
    # Get all proposals this user participates in
    query = db.select(Participation).where(Participation.user_id == user.id)
    parts = db.session.execute(query).scalars().all()
    proposals = [db.session.get(TripProposal, p.proposal_id) for p in parts]

    # Split active vs inactive
    active = [p for p in proposals if p and p.status in (ProposalStatus.open, ProposalStatus.closed_to_new_participants)]
    inactive = [p for p in proposals if p and p.status in (ProposalStatus.finalized, ProposalStatus.cancelled)]

    return render_template("profile_view.html", user=user, active_proposals=active, inactive_proposals=inactive)



@auth_bp.route("/profile/edit", methods=["GET", "POST"])
@login_required
def profile_edit():
    form = ProfileForm(request.form if request.method == "POST" else None)
    if request.method == "POST" and form.validate():
        current_user.alias = form.alias.data.strip()
        current_user.description = form.description.data
        
        # Handle password change
        new_password = request.form.get("new_password", "").strip()
        confirm_password = request.form.get("confirm_password", "").strip()
        
        if new_password or confirm_password:
            if not new_password:
                flash("Please enter a new password.", "danger")
                return render_template("profile_edit.html", form=form)
            if new_password != confirm_password:
                flash("Passwords do not match.", "danger")
                return render_template("profile_edit.html", form=form)
            if len(new_password) < 6:
                flash("Password must be at least 6 characters long.", "danger")
                return render_template("profile_edit.html", form=form)
            
            # Update password
            current_user.password_hash = generate_password_hash(new_password)
            flash("Profile and password updated.", "success")
        else:
            flash("Profile updated.", "success")
        
        db.session.commit()
        return redirect(url_for("proposals.list_proposals"))
    
    # Prefill form on GET
    if request.method == "GET":
        form.description.data = current_user.description
        form.alias.data = current_user.alias
    return render_template("profile_edit.html", form=form)
