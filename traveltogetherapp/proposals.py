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
    """Return the participation object for the logged-in user (or None)."""
    if not current_user.is_authenticated:
        return None
    return Participation.query.filter_by(
        user_id=current_user.id, proposal_id=proposal.id
    ).first()


def _parse_meetup_datetime(req) -> datetime | None:
    """Parse meetup datetime from form data."""
    date_str = req.form.get("date", "").strip()
    time_str = req.form.get("time", "").strip()
    
    if date_str and time_str:
        try:
            return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M")
        except ValueError:
            return None
    return None


@proposals_bp.route("/proposals")
@login_required
def list_proposals():
    # Only show open or closed_to_new_participants proposals for discovery
    proposals = TripProposal.query.filter(
        TripProposal.status.in_([ProposalStatus.open, ProposalStatus.closed_to_new_participants])
    ).order_by(TripProposal.start_date.is_(None), TripProposal.start_date.asc()).all()

    # Call get_participation for each proposal
    for p in proposals:
        p.participation = get_participation(p)
    return render_template("proposals_list.html", proposals=proposals)


@proposals_bp.route("/proposal/<int:proposal_id>")
@login_required
def proposal_detail(proposal_id: int):
    proposal = TripProposal.query.get_or_404(proposal_id)

    # Require user to be a participant to view details
    participation = get_participation(proposal)
    if not participation:
        flash("You are not a participant of this trip.", "danger")
        return redirect(url_for("proposals.list_proposals"))

    # Messages - newest first
    messages = (
        Message.query.filter_by(proposal_id=proposal.id)
        .order_by(Message.timestamp.desc())
        .all()
    )

    # Meetups - NULL (unknown datetime) last
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
        participation=participation,   # IMPORTANT: used in template to show delete button
        ProposalStatus=ProposalStatus,  # Pass enum to template
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

    proposal = TripProposal.query.get(proposal_id)
    
    # If this is the last participant, delete the entire proposal
    participant_count = len(proposal.participations)
    if participant_count <= 1:
        Message.query.filter_by(proposal_id=proposal.id).delete()
        Meetup.query.filter_by(proposal_id=proposal.id).delete()
        Participation.query.filter_by(proposal_id=proposal.id).delete()
        db.session.delete(proposal)
        db.session.commit()
        flash("You were the last participant. The trip proposal has been deleted.", "success")
        return redirect(url_for("proposals.list_proposals"))
    
    # Otherwise just remove this participant
    db.session.delete(participation)

    # If trip was closed due to max participants, reopen if space available
    if proposal.status == ProposalStatus.closed_to_new_participants:
        if proposal.max_participants and len(proposal.participations) - 1 < proposal.max_participants:
            proposal.status = ProposalStatus.open

    db.session.commit()
    flash("You left the trip.", "success")
    return redirect(url_for("proposals.list_proposals"))

@proposals_bp.route("/proposal/new", methods=["GET", "POST"])
@login_required
def new_proposal():
    if request.method == "POST":
        title = request.form.get("title", "").strip()
        departure_location = request.form.get("departure_location", "").strip()
        destination = request.form.get("destination", "").strip()
        activities = request.form.get("activities", "").strip()

        # Budget (float)
        budget = None
        budget_raw = request.form.get("budget", "").strip()
        if budget_raw:
            try:
                budget = float(budget_raw)
            except ValueError:
                pass

        # Max participants (int)
        max_participants = None
        mp_raw = request.form.get("max_participants", "").strip()
        if mp_raw:
            try:
                max_participants = int(mp_raw)
            except ValueError:
                pass

        # Dates
        start_date = None
        end_date = None
        start_date_raw = request.form.get("start_date", "").strip()
        end_date_raw = request.form.get("end_date", "").strip()
        
        if start_date_raw:
            try:
                start_date = datetime.strptime(start_date_raw, "%Y-%m-%d").date()
            except ValueError:
                pass
        
        if end_date_raw:
            try:
                end_date = datetime.strptime(end_date_raw, "%Y-%m-%d").date()
            except ValueError:
                pass

        # Boolean fields for marking information as final
        departure_location_is_final = request.form.get("departure_location_is_final") == "on"
        destination_is_final = request.form.get("destination_is_final") == "on"
        budget_is_final = request.form.get("budget_is_final") == "on"
        dates_are_final = request.form.get("dates_are_final") == "on"
        activities_are_final = request.form.get("activities_are_final") == "on"

        if not title:
            flash("Title is required.", "danger")
            return render_template("proposal_create_new.html")

        proposal = TripProposal(
            title=title,
            departure_location=departure_location,
            destination=destination,
            budget=budget,
            max_participants=max_participants,
            start_date=start_date,
            end_date=end_date,
            activities=activities,
            departure_location_is_final=departure_location_is_final,
            destination_is_final=destination_is_final,
            budget_is_final=budget_is_final,
            dates_are_final=dates_are_final,
            activities_are_final=activities_are_final,
            creator_id=current_user.id,
        )
        db.session.add(proposal)
        db.session.commit()

        # Automatically add creator as participant with edit rights
        part = Participation(user_id=current_user.id, proposal_id=proposal.id, can_edit=True)
        db.session.add(part)
        db.session.commit()

        flash("Trip proposal created successfully.", "success")
        return redirect(url_for("proposals.list_proposals"))

    return render_template("proposal_create_new.html")


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


@proposals_bp.route("/proposal/<int:proposal_id>/grant-edit/<int:user_id>", methods=["POST"])
@login_required
def grant_edit_permission(proposal_id: int, user_id: int):
    proposal = TripProposal.query.get_or_404(proposal_id)
    participation = get_participation(proposal)
    if not participation or not participation.can_edit:
        flash("You do not have permission to grant edit rights.", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))
    target = Participation.query.filter_by(proposal_id=proposal_id, user_id=user_id).first()
    if not target:
        flash("User is not a participant.", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))
    if target.can_edit:
        flash("User already has edit rights.", "info")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))
    target.can_edit = True
    db.session.commit()
    flash("Edit rights granted.", "success")
    return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

@proposals_bp.route("/proposal/<int:proposal_id>/delete", methods=["POST"])
@login_required
def delete_proposal(proposal_id: int):
    """Delete a proposal (only for users with can_edit permission)."""
    proposal = TripProposal.query.get_or_404(proposal_id)

    participation = get_participation(proposal)
    if not participation or not participation.can_edit:
        flash("You do not have permission to delete this proposal.", "danger")
        return redirect(url_for("proposals.proposal_detail", proposal_id=proposal_id))

    # Clean up related rows to avoid FK errors (since there's no relationship-cascade for Participation)
    Message.query.filter_by(proposal_id=proposal.id).delete()
    Meetup.query.filter_by(proposal_id=proposal.id).delete()
    Participation.query.filter_by(proposal_id=proposal.id).delete()

    db.session.delete(proposal)
    db.session.commit()

    flash("Proposal deleted successfully.", "success")
    return redirect(url_for("proposals.list_proposals"))
