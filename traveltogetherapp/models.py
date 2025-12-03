from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import enum
from datetime import datetime

db = SQLAlchemy()

class ProposalStatus(enum.Enum):
    open = 1
    closed_to_new_participants = 2
    finalized = 3
    cancelled = 4

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    # Optional display alias shown across the site (e.g., "Alex", "Traveller123")
    alias = db.Column(db.String(50), nullable=True)

    # Relasjoner
    messages = db.relationship("Message", backref="author", lazy=True)
    created_proposals = db.relationship("TripProposal", backref="creator", lazy=True)

class TripProposal(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100))
    budget = db.Column(db.Float, nullable=True)
    max_participants = db.Column(db.Integer, nullable=True)
    start_date = db.Column(db.Date, nullable=True)
    end_date = db.Column(db.Date, nullable=True)
    status = db.Column(db.Enum(ProposalStatus), default=ProposalStatus.open)

    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)

    participations = db.relationship(
        "Participation",
        backref="proposal_parent",
        lazy=True,
        cascade="all, delete-orphan"
    )

    # Relasjoner
    messages = db.relationship("Message", backref="proposal", lazy=True, cascade="all, delete-orphan")
    meetups = db.relationship("Meetup", backref="proposal", lazy=True, cascade="all, delete-orphan")

class Participation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    proposal_id = db.Column(db.Integer, db.ForeignKey("trip_proposal.id"))
    can_edit = db.Column(db.Boolean, default=False)
    
    # Relationship to User
    user = db.relationship("User", backref="participations", lazy=True)

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(db.Text, nullable=True)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"))
    proposal_id = db.Column(db.Integer, db.ForeignKey("trip_proposal.id"))

class Meetup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    location = db.Column(db.String(100), nullable=True)
    datetime = db.Column(db.DateTime, nullable=True)
    proposal_id = db.Column(db.Integer, db.ForeignKey("trip_proposal.id"))
    creator_id = db.Column(db.Integer, db.ForeignKey("user.id"))
