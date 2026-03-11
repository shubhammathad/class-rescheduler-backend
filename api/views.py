from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from rest_framework.permissions import AllowAny, IsAuthenticated
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta

from .models import Teacher, ClassSession, LeaveRequest
from .serializers import TeacherSerializer

# --- 1. AUTHENTICATION ---
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    username, password = request.data.get('username'), request.data.get('password')
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        return Response({'token': str(token.key), 'full_name': str(user.first_name or user.username), 'username': str(user.username)})
    return Response({'error': 'Invalid credentials'}, status=400)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        data = TeacherSerializer(teacher).data
        data['full_name'] = str(request.user.first_name or request.user.username)
        return Response(data)
    except: return Response({"error": "Not found"}, status=404)

# --- 2. SCHEDULE LOGIC (VANISHING CLASSES + FUZZY ROOM MATCHING) ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_weekly_schedule(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        sessions = ClassSession.objects.filter(teacher=teacher)
        days_map = {"Monday": 0, "0": 0, "00": 0, "Tuesday": 1, "1": 1, "Wednesday": 2, "2": 2, "Thursday": 3, "3": 3, "Friday": 4, "4": 4, "Saturday": 5, "5": 5, "06": 5, "6": 5, "Sunday": 6}

        my_filled = LeaveRequest.objects.filter(requester=teacher, status='FILLED')
        i_am_covering = LeaveRequest.objects.filter(final_substitute=teacher, status='FILLED')

        static_data = []
        for s in sessions:
            day_idx = days_map.get(str(s.day).strip(), 0)
            # VANISHING LOGIC: Hide if someone is already subbing this
            is_covered = any(req.time_slot.hour == s.start_time.hour and req.date.weekday() == day_idx for req in my_filled)
            if not is_covered:
                static_data.append({'id': s.id, 'subject_name': str(s.subject.name), 'day': day_idx, 'start_time': s.start_time.strftime("%H:%M:%S"), 'room_number': str(s.room_number or "N/A"), 'is_substitution': False})

        for sub in i_am_covering:
            w_idx, day_name = sub.date.weekday(), sub.date.strftime('%A')
            # LOOKUP: Search variations to find the room
            orig = ClassSession.objects.filter(teacher=sub.requester, day__in=[day_name, str(w_idx), f"0{w_idx}", f"{w_idx}", f"{w_idx+1}"], start_time__hour=sub.time_slot.hour).first()
            static_data.append({'id': f"sub_{sub.id}", 'subject_name': f"SUB: {orig.subject.name}" if (orig and orig.subject) else "Substitution", 'day': w_idx, 'start_time': sub.time_slot.strftime("%H:%M:%S"), 'room_number': str(orig.room_number) if orig else "Room?", 'is_substitution': True})
        return Response({"regular_schedule": static_data, "upcoming_substitutions": []})
    except Exception as e: return Response({"error": str(e)}, status=200)

# --- 3. TEACHER SEARCH & MY REQUESTS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def available_teachers(request):
    try:
        current_teacher = Teacher.objects.get(user=request.user)
        other_teachers = Teacher.objects.exclude(id=current_teacher.id)
        data = [{'id': int(t.id), 'full_name': str(t.user.get_full_name() or t.user.username), 'subjects_display': ", ".join([str(subj.name).upper() for subj in t.subjects.all()])} for t in other_teachers]
        return Response(data, status=200)
    except: return Response([], status=200)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_my_requests(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        all_reqs = LeaveRequest.objects.filter(requester=teacher).order_by('-created_at')
        data = []
        for r in all_reqs:
            sub_name = r.final_substitute.user.username if r.final_substitute else ""
            msg = f"Accepted by {sub_name}" if r.status == 'FILLED' else f"Rejected: {r.rejection_reason}" if r.status == 'REJECTED' else f"Status: {r.status}"
            data.append({'id': r.id, 'date': r.date.strftime("%d-%m-%Y"), 'time': r.time_slot.strftime("%H:%M:%S"), 'status': str(r.status), 'message': str(msg)})
        return Response(data)
    except: return Response([], status=200)

# --- 4. WORKFLOW ACTIONS ---
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def pending_substitutions(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        reqs = LeaveRequest.objects.filter(status='APPROVED_OPEN').exclude(requester=teacher)
        data = [{'id': r.id, 'requester_name': str(r.requester.user.first_name or r.requester.user.username), 'date': r.date.strftime("%d-%m-%Y"), 'start_time': r.time_slot.strftime("%H:%M:%S"), 'reason': str(r.reason), 'subjects_display': ", ".join([str(s.name).upper() for s in r.requester.subjects.all()])} for r in reqs]
        return Response(data, status=200)
    except: return Response([], status=200)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_request(request):
    try:
        teacher = Teacher.objects.get(user=request.user)
        LeaveRequest.objects.create(requester=teacher, date=request.data.get('date'), time_slot=request.data.get('time_slot'), reason=request.data.get('reason', ''), status='PENDING_HOD')
        return Response({"message": "Created"}, status=201)
    except Exception as e: return Response({"error": str(e)}, status=400)

@api_view(['POST'])
def respond_to_request(request, request_id):
    req = get_object_or_404(LeaveRequest, id=request_id)
    action, responder = request.data.get('action', '').upper(), Teacher.objects.get(user=request.user)
    if action == 'ACCEPT': req.status, req.final_substitute = 'FILLED', responder
    elif action == 'REJECT': req.status, req.final_substitute, req.rejection_reason = 'REJECTED', responder, request.data.get('reason', 'No reason provided')
    req.save()
    return Response({"message": "Success"})

@api_view(['POST'])
def hod_action(request, request_id):
    req = get_object_or_404(LeaveRequest, id=request_id)
    req.status = 'APPROVED_OPEN'
    req.save()
    return Response({"message": "Approved"})