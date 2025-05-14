from flask import Blueprint, request, jsonify
from flask_restful import Api, Resource
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity
from extensions import db
from models import User, Branch, Role, Shift, Event, Participant
from datetime import datetime

admin_bp = Blueprint('admin', __name__)
api = Api(admin_bp)

class GetAdminDetails(Resource):
    @jwt_required()
    def get(self):
        user = User.query.get(get_jwt_identity())

        if user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        return {
            'name': f'{user.first_name} {user.last_name}',
            'branch_id': user.branch_id,
            'branch_name': user.branch.city if user.branch else None,
            'role': user.role_obj.name
        }

class GetAllBranches(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user:
            return {'message': 'Unauthorized'}, 403

        role = current_user.role_obj.name

        if role == 'אדמין':
            branches = Branch.query.all()
        elif role == 'מנהל סניף':
            branches = [current_user.branch] if current_user.branch else []
        else:
            return {'message': 'אין הרשאה לצפות בסניפים'}, 403

        return {
            'branches': [{'id': b.id, 'name': b.city} for b in branches]
        }
class UserRegistration(Resource):
    @jwt_required()
    def post(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        data = request.get_json()
        required_fields = ['first_name', 'last_name', 'email', 'password', 'role']

        for field in required_fields:
            if field not in data or not data.get(field):
                return {'message': f'{field} is required'}, 400

        if current_user.role_obj.name == 'אדמין' and not data.get('branch_id'):
            return {'message': 'branch_id is required'}, 400

        if current_user.role_obj.name == 'מנהל סניף' and data.get('role') == 'אדמין':
            return {'message': 'אין הרשאה ליצור משתמש מסוג אדמין'}, 403

        branch_id = (
            current_user.branch_id if current_user.role_obj.name == 'מנהל סניף'
            else data.get('branch_id')
        )

        if User.query.filter_by(email=data['email']).first():
            return {'message': 'User already exists'}, 400

        role = Role.query.filter_by(name=data['role']).first()
        if not role:
            return {'message': 'Role not found'}, 400

        new_user = User(
            first_name=data['first_name'],
            last_name=data['last_name'],
            email=data['email'],
            role_id=role.id,
            branch_id=branch_id,
            birth_date=data.get('birth_date')
        )
        new_user.set_password(data['password'])

        db.session.add(new_user)
        db.session.commit()

        access_token = create_access_token(identity=str(new_user.id))
        return {'access_token': access_token, 'access_id': new_user.id}, 200


class GetAllShiftsForAdmin(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if not current_user or current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        query = db.session.query(Shift, Branch, User).join(Branch, Shift.branch_id == Branch.id).join(User, Shift.user_id == User.id)

        if current_user.role_obj.name == 'מנהל סניף':
            query = query.filter(Shift.branch_id == current_user.branch_id)

        shifts = query.all()

        shift_data = [
            {
                'user': f"{user.first_name} {user.last_name}",
                'date': shift.date.strftime('%Y-%m-%d'),
                'shiftType': shift.shiftType,
                'location': shift.location,
                'branch': branch.city
            }
            for shift, branch, user in shifts
        ]
        return {'status': 'success', 'data': shift_data}

class EventsWithParticipants(Resource):
    @jwt_required()
    def get(self):
        current_user = User.query.get(get_jwt_identity())

        if current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        if current_user.role_obj.name == 'אדמין':
            events = Event.query.all()
        else:
            events = Event.query.filter_by(branch_id=current_user.branch_id).all()

        output = []
        for event in events:
            participants = [
                {
                    'name': f'{p.user.first_name} {p.user.last_name}'
                }
                for p in event.participants if p.user
            ]
            output.append({
                'id': event.id,
                'date': event.date.strftime('%Y-%m-%d') if not isinstance(event.date, str) else event.date,
                'event_description': event.event_description,
                'lecturer_name': event.lecturer_name,
                'branch_city': event.branch.city if event.branch else '',
                'participants': participants
            })

        return jsonify(output)

class DeleteEvent(Resource):
    @jwt_required()
    def delete(self, event_id):
        current_user = User.query.get(get_jwt_identity())

        if current_user.role_obj.name not in ['אדמין', 'מנהל סניף']:
            return {'message': 'Unauthorized'}, 403

        event = Event.query.get(event_id)
        if not event:
            return {'message': 'Event not found'}, 404

        if current_user.role_obj.name == 'מנהל סניף' and event.branch_id != current_user.branch_id:
            return {'message': 'אין לך הרשאה למחוק את האירוע הזה'}, 403

        Participant.query.filter_by(event_id=event.id).delete()
        db.session.delete(event)
        db.session.commit()

        return {'message': 'Event deleted successfully'}, 200

# רישום הריסורסים
api.add_resource(GetAdminDetails, '/getadmin')
api.add_resource(UserRegistration, '/register')
api.add_resource(GetAllBranches, '/branches')
api.add_resource(GetAllShiftsForAdmin, '/allshifts')
api.add_resource(EventsWithParticipants, '/events_with_participants')
api.add_resource(DeleteEvent, '/calendar/event/<int:event_id>')
