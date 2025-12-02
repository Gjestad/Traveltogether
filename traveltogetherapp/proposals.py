from flask import Blueprint, render_template, redirect, url_for, request, flash, current_app
from flask_login import login_required, current_user
from datetime import datetime
import re

from .models import (
    db,
    TripProposal,
    Participation,
    ProposalStatus,
    Message,
    Meetup,
)

# Blueprint
proposals_bp = Blueprint("proposals", __name__)


def get_participation(proposal: TripProposal):
    """Returner deltagelsesobjektet for innlogget bruker (eller None)."""
    if not current_user.is_authenticated:
        return None
    return Participation.query.filter_by(
        user_id=current_user.id, proposal_id=proposal.id
    ).first()


def _parse_meetup_datetime(req) -> datetime | None:
    """
    Godtar:
      - 'date' (YYYY-MM-DD) + 'time' (HH:MM, H:MM, HH:MM:SS, H:MM:SS, samt '.' eller '-' som separator)
      - fallback 'datetime' (YYYY-MM-DDTHH:MM[,SS]) fra <input type="datetime-local"> eller vårt skjulte felt
    Returnerer naiv datetime (lokal tid) eller None.
    """
    date_str = (req.form.get("date") or "").strip()
    time_str = (req.form.get("time") or "").strip() or (req.form.get("time_text") or "").strip()
    dt_raw  = (req.form.get("datetime") or "").strip()

    try:
        current_app.logger.info(f"[meetup] form: date='{date_str}' time='{time_str}' datetime='{dt_raw}'")
    except Exception:
        pass

    # --- Helper: normaliser tid til HH:MM ---
    # Tillat 6:18, 06:18, 06:18:00, 6:18:00, 06.18, 06-18
    def norm_time(s: str) -> str | None:
        if not s:
            return None
        s = s.strip()
        s = s.replace(".", ":").replace("-", ":")
        m = re.match(r"^(\d{1,2}):(\d{2})(?::(\d{2}))?$", s)
        if not m:
            return None
        h = int(m.group(1))
        mi = int(m.group(2))
        if not (0 <= h <= 23 and 0 <= mi <= 59):
            return None
        return f"{h:02d}:{mi:02d}"

    # 1) Foretrekk separate felter
    hhmm = norm_time(time_str)
    if date_str and hhmm:
        try:
            return datetime.strptime(f"{date_str} {hhmm}", "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
            except ValueError:
                return None

    # 2) Fallback: datetime-local / skjult datetime-felt
    if dt_raw:
        v = dt_raw.strip().replace(" ", "T")
        try:
            return datetime.fromisoformat(v)  # YYYY-MM-DDTHH:MM[:SS[.ffffff]]
        except ValueError:
            pass
        for fmt in ("%Y-%m-%dT%H:%M", "%Y-%m-%dT%H:%M:%S"):
            try:
                return datetime.strptime(v, fmt)
            except ValueError:
                continue

    return None


@proposals_bp.route("/proposals")
@login_required
def list_proposals():
    # Only show open or closed_to_new_participants proposals for discovery
    proposals = TripProposal.query.filter(
        TripProposal.status.in_([ProposalStatus.open, ProposalStatus.closed_to_new_participants])
    ).all()

    # Call get_participation for each proposal
    for p in proposals:
        p.participation = get_participation(p)
    return render_template("proposals_list.html", proposals=proposals)


@proposals_bp.route("/proposal/<int:proposal_id>")
@login_required
def proposal_detail(proposal_id: int):
    proposal = TripProposal.query.get_or_404(proposal_id)

    # Krev at bruker deltar for å se detaljer
    participation = get_participation(proposal)
    if not participation:
        flash("You are not a participant of this trip.", "danger")
        return redirect(url_for("proposals.list_proposals"))

    # Meldinger – nyeste først
    messages = (
        Message.query.filter_by(proposal_id=proposal.id)
        .order_by(Message.timestamp.desc())
        .all()
    )

    # Meetups – NULL (ukjent tidspunkt) til slutt
    meetups = (
        Meetup.query.filter_by(proposal_id=proposal.id)
        .order_by(Meetup.datetime.is_(None), Meetup.datetime.desc())
        .all()
    )

    return render_template(
        "proposal_detail.html",
        proposal=proposal,
        messages=messages,
        meetups=meetups,
        participation=participation,   # VIKTIG: brukes i templaten for å vise delete-knappen
    )

@proposals_bp.route("/proposal/<int:proposal_id>/join")
@login_required
def proposal_join(proposal_id: int):
    proposal = TripProposal.query.get_or_404(proposal_id)
    
    # already participating 
    if get_participation(proposal):
       return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))
    
    # check if proposal is open to new participants
    if proposal.status != ProposalStatus.open:
        flash("This proposal is no longer accepting new participants.", "warning")
        return redirect(url_for("proposals.list_proposals"))
    
    # check if trip is full 
    if proposal.max_participants and len(proposal.participations) >= proposal.max_participants:
        flash("This trip is full.", "warning")
        # auto-close proposal
        proposal.status = ProposalStatus.closed_to_new_participants
        db.session.commit()
        return redirect(url_for("proposals.list_proposals"))
    
    # Add participation
    participation = Participation(user_id=current_user.id, proposal_id=proposal_id)
    db.session.add(participation)

    # close if full after joining
    if proposal.max_participants and len(proposal.participations) + 1 >= proposal.max_participants:
        proposal.status = ProposalStatus.closed_to_new_participants

    db.session.commit()
     
    return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

@proposals_bp.route("/proposal/<int:proposal_id>/leave")
@login_required
def proposal_leave(proposal_id: int):
    participation = Participation.query.filter_by(
        proposal_id=proposal_id,
        user_id=current_user.id
    ).first()
    
    if not participation:
        flash("You are not participating in this trip.", "info")
        return redirect(url_for("proposals.list_proposals"))

    db.session.delete(participation)

    # If trip was closed due to max participants, reopen if space available
    proposal = TripProposal.query.get(proposal_id)
    if proposal.status == ProposalStatus.closed_to_new_participants:
        if proposal.max_participants and proposal.participations.count() < proposal.max_participants:
            proposal.status = ProposalStatus.open

   #TODO: If a participant wanting to leave a trip proposal that has not been finalized or cancelled yet is the only one with editing permissions for it, the application will not allow them to leave. 

    db.session.commit()
    flash("You left the trip.", "success")
    return redirect(url_for("proposals.list_proposals"))

@proposals_bp.route("/proposal/new", methods=["GET", "POST"])
@login_required
def new_proposal():
    if request.method == "POST":
        title = (request.form.get("title") or "").strip()
        destination = (request.form.get("destination") or "").strip()
        departure = (request.form.get("departure") or "").strip()

        # Budsjett (float)
        budget_raw = (request.form.get("budget") or "").strip()
        try:
            budget = float(budget_raw) if budget_raw else None
        except ValueError:
            budget = None

        # Maks deltakere (int)
        mp_raw = (request.form.get("max_participants") or "").strip()
        try:
            max_participants = int(mp_raw) if mp_raw else None
        except ValueError:
            max_participants = None

        if not title:
            flash("Title is required.", "danger")
            return render_template("proposal_new.html")

        proposal = TripProposal(
            title=title,
            destination=destination or None,
            departure=departure or None,
            budget=budget,
            max_participants=max_participants,
            creator_id=current_user.id,
        )
        db.session.add(proposal)
        db.session.commit()

        # Legg automatisk til skaperen som deltaker med redigeringsrett
        part = Participation(user_id=current_user.id, proposal_id=proposal.id, can_edit=True)
        db.session.add(part)
        db.session.commit()

        flash("Trip proposal created successfully.", "success")
        return redirect(url_for("proposals.list_proposals"))

    return render_template("proposal_new.html")


@proposals_bp.route("/proposal/<int:proposal_id>/message", methods=["POST"])
@login_required
def post_message(proposal_id: int):
    body = (request.form.get("body") or "").strip()
    if not body:
        flash("Message cannot be empty.", "warning")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    proposal = TripProposal.query.get_or_404(proposal_id)
    if not get_participation(proposal):
        flash("You are not a participant of this trip.", "danger")
        return redirect(url_for("proposals.list_proposals"))

    # Prevent posting messages on finalized or cancelled proposals
    if proposal.status in (ProposalStatus.finalized, ProposalStatus.cancelled):
        flash("This trip proposal is no longer accepting messages.", "warning")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    msg = Message(content=body, user_id=current_user.id, proposal_id=proposal_id)
    db.session.add(msg)
    db.session.commit()
    flash("Message posted!", "success")
    return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))


@proposals_bp.route("/proposal/<int:proposal_id>/meetup", methods=["POST"])
@login_required
def add_meetup(proposal_id: int):
    location = (request.form.get("location") or "").strip()

    dt = _parse_meetup_datetime(request)
    if not dt:
        try:
            current_app.logger.warning(f"[meetup] parse failed. form={dict(request.form)}")
        except Exception:
            pass
        flash("Please provide a valid date and time (e.g. 2025-11-12 and 06:18).", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    proposal = TripProposal.query.get_or_404(proposal_id)
    if not get_participation(proposal):
        flash("You are not a participant of this trip.", "danger")
        return redirect(url_for("proposals.list_proposals"))

    # Prevent adding meetups on finalized or cancelled proposals
    if proposal.status in (ProposalStatus.finalized, ProposalStatus.cancelled):
        flash("This trip proposal is no longer accepting changes.", "warning")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    meetup = Meetup(
        location=location or None,
        datetime=dt,
        proposal_id=proposal_id,
        creator_id=current_user.id,
    )
    db.session.add(meetup)
    db.session.commit()

    flash("Meetup added!", "success")
    return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))


@proposals_bp.route("/proposal/<int:proposal_id>/finalize", methods=["POST"])
@login_required
def finalize_proposal(proposal_id: int):
    """Finalize a proposal - make it read-only and no longer discoverable."""
    proposal = TripProposal.query.get_or_404(proposal_id)

    participation = get_participation(proposal)
    if not participation or not participation.can_edit:
        flash("You do not have permission to finalize this proposal.", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    if proposal.status in (ProposalStatus.finalized, ProposalStatus.cancelled):
        flash("This proposal has already been finalized or cancelled.", "warning")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    proposal.status = ProposalStatus.finalized
    db.session.commit()

    flash("Proposal finalized successfully. It is now read-only.", "success")
    return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))


@proposals_bp.route("/proposal/<int:proposal_id>/cancel", methods=["POST"])
@login_required
def cancel_proposal(proposal_id: int):
    """Cancel a proposal - make it read-only and no longer discoverable."""
    proposal = TripProposal.query.get_or_404(proposal_id)

    participation = get_participation(proposal)
    if not participation or not participation.can_edit:
        flash("You do not have permission to cancel this proposal.", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    if proposal.status in (ProposalStatus.finalized, ProposalStatus.cancelled):
        flash("This proposal has already been finalized or cancelled.", "warning")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    proposal.status = ProposalStatus.cancelled
    db.session.commit()

    flash("Proposal cancelled successfully. It is now read-only.", "success")
    return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))


@proposals_bp.route("/proposal/<int:proposal_id>/close-to-new-participants", methods=["POST"])
@login_required
def close_to_new_participants_proposal(proposal_id: int):
    """Close a proposal to new participants - no new joins allowed but other functionality continues."""
    proposal = TripProposal.query.get_or_404(proposal_id)

    participation = get_participation(proposal)
    if not participation or not participation.can_edit:
        flash("You do not have permission to close this proposal to new participants.", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    if proposal.status != ProposalStatus.open:
        flash("This proposal is not open to new participants.", "warning")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    proposal.status = ProposalStatus.closed_to_new_participants
    db.session.commit()

    flash("Proposal closed to new participants. Existing functionality remains available.", "success")
    return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))


@proposals_bp.route("/proposal/<int:proposal_id>/delete", methods=["POST"])
@login_required
def delete_proposal(proposal_id: int):
    """Slett en proposal (kun for brukere med can_edit på denne)."""
    proposal = TripProposal.query.get_or_404(proposal_id)

    participation = get_participation(proposal)
    if not participation or not participation.can_edit:
        flash("You do not have permission to delete this proposal.", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    # Rydd relaterte rader for å unngå FK-feil (siden det ikke finnes relationship-cascade for Participation)
    Message.query.filter_by(proposal_id=proposal.id).delete()
    Meetup.query.filter_by(proposal_id=proposal.id).delete()
    Participation.query.filter_by(proposal_id=proposal.id).delete()

    db.session.delete(proposal)
    db.session.commit()

    flash("Proposal deleted successfully.", "success")
    return redirect(url_for("proposals.list_proposals"))
