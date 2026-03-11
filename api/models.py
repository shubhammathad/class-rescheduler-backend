from django.db import models
from django.contrib.auth.models import User

# --- 1. STATIC DATA ---
class Department(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True)
    def __str__(self): return self.name

class Subject(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=20, unique=True)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    def __str__(self): return self.name

class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    department = models.ForeignKey(Department, on_delete=models.CASCADE)
    subjects = models.ManyToManyField(Subject, related_name='qualified_teachers')
    is_hod = models.BooleanField(default=False)
    fcm_token = models.CharField(max_length=255, blank=True, null=True)
    def __str__(self): return self.user.get_full_name()

# --- 2. RECURRING SCHEDULE ---
class ClassSession(models.Model):
    day = models.CharField(max_length=20)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room_number = models.CharField(max_length=20)
    class Meta:
        unique_together = ('teacher', 'day', 'start_time')
    def __str__(self): return f"{self.subject} - {self.day} {self.start_time}"

# --- 3. DYNAMIC TRANSACTIONS ---
class LeaveRequest(models.Model):
    STATUS_CHOICES = [
        ('PENDING_HOD', 'Pending HOD Approval'),
        ('APPROVED_OPEN', 'Approved - Waiting for Sub'),
        ('FILLED', 'Filled by Substitute'),
        ('REJECTED', 'Rejected'),
        ('CANCELLED', 'Cancelled'),
    ]
    requester = models.ForeignKey(Teacher, related_name='requests_made', on_delete=models.CASCADE)
    date = models.DateField()
    time_slot = models.TimeField()
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING_HOD')
    rejection_reason = models.TextField(null=True, blank=True)
    final_substitute = models.ForeignKey(Teacher, related_name='substitutions_filled',
                                         null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)
    def __str__(self): return f"{self.requester} - {self.date} ({self.status})"

class SubstitutionProposal(models.Model):
    request = models.ForeignKey(LeaveRequest, related_name='proposals', on_delete=models.CASCADE)
    candidate = models.ForeignKey(Teacher, on_delete=models.CASCADE)
    is_accepted = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    class Meta:
        unique_together = ('request', 'candidate')