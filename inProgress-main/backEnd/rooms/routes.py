from flask import Blueprint, request
from flask_restful import Resource, Api
from flask_jwt_extended import jwt_required, get_jwt_identity
from models import db, RoomReservation, User
from datetime import datetime

rooms_bp = Blueprint('rooms', __name__)
api = Api(rooms_bp)

class UserProfile(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())

        if not user:
            return {"status": "fail", "message": "User not found"}, 404

        return {
            "first_name": user.first_name,
            "last_name": user.last_name,
            "email": user.email,
            "role": user.role_obj.name,
            "branch": {
                "id": user.branch.id,
                "city": user.branch.city
            }
        }

class AddRoomReservation(Resource):
    @jwt_required()
    def post(self):
        data = request.get_json()
        date_str = data.get('date')
        hour = data.get('hour')
        room_name = data.get('room_name')

        if not all([date_str, hour, room_name]):
            return {"status": "fail", "message": "Missing data"}, 400

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return {"status": "fail", "message": "Invalid date format"}, 400

        user = User.query.get(get_jwt_identity())

        existing_reservation = RoomReservation.query.filter_by(
            date=date,
            hour=hour,
            room_name=room_name,
            branch_id=user.branch_id
        ).first()

        if existing_reservation:
            return {"status": "fail", "message": "Room already reserved in your branch"}, 409

        reservation = RoomReservation(
            date=date,
            hour=hour,
            room_name=room_name,
            user_id=user.id,
            branch_id=user.branch_id
        )

        db.session.add(reservation)
        db.session.commit()

        return {"status": "success", "message": "Room reserved successfully"}

class GetAllRoomReservations(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())
        reservations = RoomReservation.query.filter_by(branch_id=user.branch_id).all()
        data = [
            {
                "date": r.date.strftime('%Y-%m-%d'),
                "hour": r.hour,
                "room_name": r.room_name,
                "user": f"{r.user.first_name} {r.user.last_name}",
                "user_id": r.user.id,
                "branch": r.branch.city
            }
            for r in reservations
        ]
        return {"status": "success", "data": data}

class GetMyReservations(Resource):
    @jwt_required()
    def get(self):
        user_id = get_jwt_identity()
        reservations = RoomReservation.query.filter_by(user_id=user_id).all()
        data = [
            {
                "date": r.date.strftime('%Y-%m-%d'),
                "hour": r.hour,
                "room_name": r.room_name,
                "branch": r.branch.city
            }
            for r in reservations
        ]
        return {"status": "success", "data": data}

class CancelRoomReservation(Resource):
    @jwt_required()
    def delete(self):
        data = request.get_json()
        date_str = data.get('date')
        hour = data.get('hour')
        room_name = data.get('room_name')

        if not all([date_str, hour, room_name]):
            return {"status": "fail", "message": "Missing data"}, 400

        try:
            date = datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return {"status": "fail", "message": "Invalid date format"}, 400

        user_id = get_jwt_identity()

        reservation = RoomReservation.query.filter_by(
            date=date,
            hour=hour,
            room_name=room_name,
            user_id=user_id
        ).first()

        if not reservation:
            return {"status": "fail", "message": "Reservation not found or not yours"}, 404

        db.session.delete(reservation)
        db.session.commit()

        return {"status": "success", "message": "Reservation canceled"}

# Register the resources with the API
api.add_resource(AddRoomReservation, '/reserve')
api.add_resource(GetAllRoomReservations, '/all')
api.add_resource(GetMyReservations, '/my') 
api.add_resource(CancelRoomReservation, '/cancel')
api.add_resource(UserProfile, '/profile')
