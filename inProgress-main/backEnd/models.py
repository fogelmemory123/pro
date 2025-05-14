from extensions import db
from werkzeug.security import generate_password_hash, check_password_hash

class Branch(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    city = db.Column(db.String(80), unique=True, nullable=False)

    users = db.relationship('User', backref='branch', lazy=True)
    events = db.relationship('Event', backref='branch', lazy=True)
    room_reservations = db.relationship('RoomReservation', backref='branch', lazy=True)
    participants = db.relationship('Participant', backref='branch', lazy=True)

    def __repr__(self):
        return f'<Branch {self.city}>'

class Role(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    users = db.relationship('User', backref='role_obj', lazy=True)

    def __repr__(self):
        return f'<Role {self.name}>'

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(80), nullable=False)
    last_name = db.Column(db.String(80), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    birth_date = db.Column(db.String(10), nullable=True)  # YYYY-MM-DD
    password_hash = db.Column(db.String(228), nullable=False)
    role_id = db.Column(db.Integer, db.ForeignKey('role.id'), nullable=False)

    shifts = db.relationship('Shift', backref='user', lazy=True)
    events = db.relationship('Event', backref='creator', lazy=True)
    room_reservations = db.relationship('RoomReservation', backref='user', lazy=True)
    participations = db.relationship('Participant', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f'<User {self.first_name} {self.last_name}>'

class Shift(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    shiftType = db.Column(db.String(80), nullable=False)
    location = db.Column(db.String(80), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)

    def __repr__(self):
        return f'<Shift {self.date} {self.shiftType} {self.location}>'

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(10), nullable=False)  # YYYY-MM-DD

    event_description = db.Column(db.String(200), nullable=False)
    lecturer_name = db.Column(db.String(100), nullable=True)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    participants = db.relationship(
        'Participant',
        backref='event',
        cascade='all, delete-orphan',
        passive_deletes=True
    )

    def __repr__(self):
        return f'<Event {self.date} {self.event_description}>'

class RoomReservation(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date, nullable=False)
    hour = db.Column(db.String(5), nullable=False)  # לדוגמה: "09:00"
    room_name = db.Column(db.String(50), nullable=False)

    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)

    def __repr__(self):
        return f'<RoomReservation {self.date} {self.hour} {self.room_name}>'

class Participant(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), nullable=False)
    event_id = db.Column(
        db.Integer,
        db.ForeignKey('event.id', ondelete='CASCADE'),
        nullable=False
    )
    branch_id = db.Column(db.Integer, db.ForeignKey('branch.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    reminder_sent = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<Participant {self.name} {self.email}>'
